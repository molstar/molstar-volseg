import base64
import json
import gemmi
from pathlib import Path
from typing import Dict, Set, Tuple, List
import zlib
import zarr
import numcodecs
import h5py
import numpy as np
import decimal
from decimal import Decimal
from preprocessor.src.preprocessors.i_data_preprocessor import IDataPreprocessor
# TODO: figure out how to specify N of downsamplings (x2, x4, etc.) in a better way
import math
from preprocessor.src.tools.magic_kernel_downsampling_3d.magic_kernel_downsampling_3d import extract_target_voxels_coords, create_x2_downsampled_grid
from sfftkrw import SFFSegmentation
from scipy import signal

VOLUME_DATA_GROUPNAME = '_volume_data'
SEGMENTATION_DATA_GROUPNAME = '_segmentation_data'
GRID_METADATA_FILENAME = 'grid_metadata.json'
ANNOTATION_METADATA_FILENAME = 'annotation_metadata.json'
# temporarly can be set to 32 to check at least x4 downsampling with 64**3 emd-1832 grid
MIN_GRID_SIZE = 100**3
DOWNSAMPLING_KERNEL = (1, 4, 6, 4, 1)


'''
class Bigclass(object):

    from classdef1 import foo, bar, baz, quux
    from classdef2 import thing1, thing2
    from classdef3 import magic, moremagic
    # unfortunately, "from classdefn import *" is an error or warning
'''


def open_zarr_structure_from_path(path: Path) -> zarr.hierarchy.Group:
    store: zarr.storage.DirectoryStore = zarr.DirectoryStore(str(path))
    # Re-create zarr hierarchy from opened store
    root: zarr.hierarchy.group = zarr.group(store=store)
    return root


class SFFPreprocessor(IDataPreprocessor):
    def __init__(self):
        # path to root of temporary storage for zarr hierarchy
        self.temp_root_path = Path(__file__).parents[1] / 'temp_zarr_hierarchy_storage'
        # path to temp storage for that entry (segmentation)
        self.temp_zarr_structure_path = None

    def preprocess(self, segm_file_path: Path, volume_file_path: Path, volume_force_dtype=np.float32):
        '''
        Returns path to temporary zarr structure that will be stored permanently using db.store
        '''
        if segm_file_path != None:
            self.__hdf5_to_zarr(segm_file_path)
        else:
            self.__initialize_empty_zarr_structure(volume_file_path)
        # Re-create zarr hierarchy
        zarr_structure: zarr.hierarchy.group = open_zarr_structure_from_path(
            self.temp_zarr_structure_path)
        
        # read map
        map_object = self.__read_volume_map_to_object(volume_file_path)
        normalized_axis_map_object = self.__normalize_axis_order(map_object)
        
        if segm_file_path != None:
            self.__process_segmentation_data(zarr_structure)
        
        self.__process_volume_data(zarr_structure, normalized_axis_map_object, volume_force_dtype)
        
        grid_metadata = self.__extract_grid_metadata(zarr_structure, normalized_axis_map_object)
        self.__temp_save_metadata(grid_metadata, GRID_METADATA_FILENAME, self.temp_zarr_structure_path)

        if segm_file_path != None:
            annotation_metadata = self.__extract_annotation_metadata(segm_file_path)
            self.__temp_save_metadata(annotation_metadata, ANNOTATION_METADATA_FILENAME, self.temp_zarr_structure_path)

        return self.temp_zarr_structure_path



    def __normalize_axis_order(self, map_object: gemmi.Ccp4Map):
        '''
        Normalizes axis order to X, Y, Z (1, 2, 3)
        '''
        # just reorders axis to X, Y, Z (https://gemmi.readthedocs.io/en/latest/grid.html#setup)
        map_object.setup(float('nan'), gemmi.MapSetup.ReorderOnly)
        ccp4_header = self.__read_ccp4_words_to_dict(map_object)
        new_axis_order = ccp4_header['MAPC'], ccp4_header['MAPR'], ccp4_header['MAPS']
        assert new_axis_order == (1, 2, 3), f'Axis order is {new_axis_order}, should be (1, 2, 3) or X, Y, Z'
        return map_object

    def __read_volume_map_to_object(self, volume_file_path: Path) -> gemmi.Ccp4Map:
        '''
        Reads ccp4 map to gemmi.Ccp4Map object 
        '''
        # https://www.ccpem.ac.uk/mrc_format/mrc2014.php
        # https://www.ccp4.ac.uk/html/maplib.html
        return gemmi.read_ccp4_map(str(volume_file_path.resolve()))

    def __process_volume_data(self, zarr_structure: zarr.hierarchy.group, map_object: gemmi.Ccp4Map, force_dtype=np.float32):
        '''
        Takes read map object, extracts volume data, downsamples it, stores to zarr_structure
        '''
        volume_data_gr: zarr.hierarchy.group = zarr_structure.create_group(VOLUME_DATA_GROUPNAME)        
        volume_arr = self.__read_volume_data(map_object, force_dtype)
        volume_downsampling_steps = self.__compute_number_of_downsampling_steps(
            MIN_GRID_SIZE,
            input_grid_size=math.prod(volume_arr.shape)
        )
        self.create_volume_downsamplings(
            original_data=volume_arr,
            downsampled_data_group=volume_data_gr,
            downsampling_steps = volume_downsampling_steps
        )

    def __process_segmentation_data(self, zarr_structure: zarr.hierarchy.group) -> None:
        '''
        Extracts segmentation data from lattice, downsamples it, stores to zarr structure
        '''
        segm_data_gr: zarr.hierarchy.group = zarr_structure.create_group(SEGMENTATION_DATA_GROUPNAME)
        value_to_segment_id_dict = self.__create_value_to_segment_id_mapping(zarr_structure)

        for gr_name, gr in zarr_structure.lattice_list.groups():
            # gr is a 'lattice' obj in lattice list
            lattice_id = int(gr.id[...])
            segm_arr = self.__lattice_data_to_np_arr(
                gr.data[0],
                gr.mode[0],
                (gr.size.cols[...], gr.size.rows[...], gr.size.sections[...])
            )
            segmentation_downsampling_steps = self.__compute_number_of_downsampling_steps(
                MIN_GRID_SIZE,
                input_grid_size=math.prod(segm_arr.shape)
            )
            # specific lattice with specific id
            lattice_gr = segm_data_gr.create_group(gr_name)
            self.__create_category_set_downsamplings(
                original_data = segm_arr,
                downsampled_data_group=lattice_gr,
                downsampling_steps = segmentation_downsampling_steps,
                value_to_segment_id_dict_for_specific_lattice_id = value_to_segment_id_dict[lattice_id]
            )

    def __compute_number_of_downsampling_steps(self, min_grid_size: int, input_grid_size: int) -> int:
        if input_grid_size <= min_grid_size:
            return 1
        num_of_downsampling_steps: int = math.ceil(math.log2(input_grid_size/min_grid_size))
        return num_of_downsampling_steps

    def __read_ccp4_words_to_dict(self, m: gemmi.Ccp4Map) -> Dict:
        ctx = decimal.getcontext()
        ctx.rounding = decimal.ROUND_CEILING
        d = {}
        d['NC'], d['NR'], d['NS'] = m.header_i32(1), m.header_i32(2), m.header_i32(3)
        d['NCSTART'], d['NRSTART'], d['NSSTART'] = m.header_i32(5), m.header_i32(6), m.header_i32(7)
        d['xLength'] = round(Decimal(m.header_float(11)), 1)
        d['yLength'] = round(Decimal(m.header_float(12)), 1)
        d['zLength'] = round(Decimal(m.header_float(13)), 1)
        d['MAPC'], d['MAPR'], d['MAPS'] = m.header_i32(17), m.header_i32(18), m.header_i32(19)
        return d

    def __extract_annotation_metadata(self, segm_file_path: Path) -> Dict:
        '''Returns processed dict of annotation metadata (some fields are removed)'''
        segm_obj = self.__open_hdf5_as_segmentation_object(segm_file_path)
        segm_dict = segm_obj.as_json()
        for lattice in segm_dict['lattice_list']:
            del lattice['data']

        return segm_dict
        # root = zarr_structure
        # root.visititems(__visitior_function_for_annotation_metadata)
    
        # d = {}
        # def __visitior_function_for_annotation_metadata(name: str, zarr_obj) -> None:
        #     '''Helper function for creating JSON with metadata'''
        #     zarr_obj_name = str(zarr_obj.name.split('/')[-1])
        
        #     if isinstance(zarr_obj, zarr.core.Array):
        #         d[zarr_obj_name] = zarr_obj[0]
        #     elif isinstance(zarr_obj, zarr.hierarchy.Group):
        #         # d[lattice]
        #         pass
        #     else:
        #         raise Exception('zarr object should be either group or array')


    def __extract_grid_metadata(self, zarr_structure: zarr.hierarchy.group, map_object) -> Dict:
        root = zarr_structure
        details = ''
        if 'details' in root:
            details = root.details[...][0].decode('utf-8')
        volume_downsamplings = sorted(root[VOLUME_DATA_GROUPNAME].array_keys())
        # convert to ints
        volume_downsamplings = sorted([int(x) for x in volume_downsamplings]) 

        # TODO:
        mean_dict = {}
        std_dict = {}
        max_dict = {}
        min_dict = {}
        grid_dimensions_dict = {}

        for arr_name, arr in root[VOLUME_DATA_GROUPNAME].arrays():
            mean_val = str(np.mean(arr[...]))
            std_val =  str(np.std(arr[...]))
            max_val = str(arr[...].max())
            min_val = str(arr[...].min())
            grid_dimensions_val: Tuple[int, int, int] = arr.shape

            mean_dict[str(arr_name)] = mean_val
            std_dict[str(arr_name)] = std_val
            max_dict[str(arr_name)] = max_val
            min_dict[str(arr_name)] = min_val
            grid_dimensions_dict[str(arr_name)] = grid_dimensions_val

        lattice_dict = {}
        lattice_ids = []
        if SEGMENTATION_DATA_GROUPNAME in root:
            for gr_name, gr in root[SEGMENTATION_DATA_GROUPNAME].groups():
                # each key is lattice id
                lattice_id = int(gr_name)

                segm_downsamplings = sorted(gr.group_keys())
                # convert to ints
                segm_downsamplings = sorted([int(x) for x in segm_downsamplings])

                lattice_dict[lattice_id] = segm_downsamplings
                lattice_ids.append(lattice_id)

        d = self.__read_ccp4_words_to_dict(map_object)

        original_voxel_size: Tuple[float, float, float] = (
            d['xLength'] / d['NC'],
            d['yLength'] / d['NR'],
            d['zLength'] / d['NS']
        )

        voxel_sizes_in_downsamplings: Dict = {}
        for rate in volume_downsamplings:
            voxel_sizes_in_downsamplings[rate] = tuple(
                [float(Decimal(i) * Decimal(rate)) for i in original_voxel_size]
            )

        # get origin of grid based on NC/NR/NSSTART variables (5, 6, 7) and original voxel size
        # Converting to strings, then to floats to make it JSON serializable (decimals are not) -> ??
        origin: Tuple[float, float, float] = (
            float(str(d['NCSTART'] * original_voxel_size[0])),
            float(str(d['NRSTART'] * original_voxel_size[1])),
            float(str(d['NSSTART'] * original_voxel_size[2])),
        )

        # get grid dimensions based on NX/NC, NY/NR, NZ/NS variables (words 1, 2, 3) in CCP4 file
        # original_grid_dimensions: Tuple[int, int, int] = (d['NC'], d['NR'], d['NS'])

        return {
            'details': details,
            'volume_downsamplings': volume_downsamplings,
            'segmentation_lattice_ids': lattice_ids,
            'segmentation_downsamplings': lattice_dict,
            # downsamplings have different voxel size so it is a dict
            'voxel_size': voxel_sizes_in_downsamplings,
            'origin': origin,
            'grid_dimensions': (d['NC'], d['NR'], d['NS']),
            'sampled_grid_dimensions': grid_dimensions_dict,
            'mean': mean_dict,
            'std': std_dict,
            'max': max_dict,
            'min': min_dict
        }

    def __temp_save_metadata(self, metadata: Dict, metadata_filename: Path, temp_dir_path: Path) -> None:
        with (temp_dir_path / metadata_filename).open('w') as fp:
            json.dump(metadata, fp)

    def __read_volume_data(self, m, force_dtype=np.float32) -> np.ndarray:
        '''
        Takes read map object (axis normalized upfront) and returns numpy arr with volume data
        '''
        # TODO: can be dask array to save memory?
        arr: np.ndarray = np.array(m.grid, dtype=force_dtype)
        # swap axes as gemmi assigns columns to 1st numpy dimension, and sections to 3rd
        # should be vise versa
        arr = arr.swapaxes(0, 2)
        return arr

    def __lattice_data_to_np_arr(self, data: str, dtype: str, arr_shape: Tuple[int, int, int]) -> np.ndarray:
        '''
        Converts lattice data to np array.
        Under the hood, decodes lattice data into zlib-zipped data, decompress it to bytes,
        and converts to np arr based on dtype (sff mode) and shape (sff size)
        '''
        decoded_data = base64.b64decode(data)
        byteseq = zlib.decompress(decoded_data)
        return np.frombuffer(byteseq, dtype=dtype).reshape(arr_shape)

    def __downsample_categorical_data(self, arr: np.ndarray, rate: int) -> np.ndarray:
        '''Returns downsampled (every other value) np array'''
        if rate == 1:
            return arr
        # TODO: if choosing between '0' and non-zero value, it should perhaps leave non-zero value
        return arr[::rate, ::rate, ::rate]
    
    def __downsample_numerical_data(self, arr: np.ndarray, rate: int) -> np.ndarray:
        '''Deprecated. Returns downsampled (mean) np array'''
        if rate == 1:
            return arr
        # return block_reduce(arr, block_size=(rate, rate, rate), func=np.mean)
        # return downsample_using_magic_kernel(arr, DOWNSAMPLING_KERNEL)

    def __create_volume_downsamplings(self, original_data: np.ndarray, downsampling_steps: int, downsampled_data_group: zarr.hierarchy.Group):
        '''
        Take original volume data, do all downsampling levels and store in zarr struct one by one
        '''
        # TODO: do we need to make it uniform float64 as other other level grids? x1 is float32
        # original_data = original_data.astype(np.float)
        current_level_data = original_data
        self.__store_single_volume_downsampling_in_zarr_stucture(current_level_data, downsampled_data_group, 1)
        for i in range(downsampling_steps):
            current_ratio = 2**(i + 1)
            
            # switching to convolve
            # downsampled_data = downsample_using_magic_kernel(current_level_data, DOWNSAMPLING_KERNEL)
            kernel = self.generate_kernel_3d_arr(list(DOWNSAMPLING_KERNEL))
            downsampled_data = signal.convolve(current_level_data, kernel, mode='same', method='fft')
            downsampled_data = downsampled_data[::2, ::2, ::2]
            
            self.__store_single_volume_downsampling_in_zarr_stucture(downsampled_data, downsampled_data_group, current_ratio)
            current_level_data = downsampled_data
        # # TODO: figure out compression/filters: b64 encoded zlib-zipped .data is just 8 bytes
        # downsamplings sizes in raw uncompressed state are much bigger 
        # TODO: figure out what to do with chunks - currently their size is not optimized

    def __store_single_volume_downsampling_in_zarr_stucture(self, downsampled_data: np.ndarray, downsampled_data_group: zarr.hierarchy.Group, ratio: int):
        downsampled_data_group.create_dataset(
            data=downsampled_data,
            name=str(ratio),
            shape=downsampled_data.shape,
            dtype=downsampled_data.dtype,
            # # TODO: figure out how to determine optimal chunk size depending on the data
            chunks=(50, 50, 50)
        )

    def __create_category_set_downsamplings(
        self,
        original_data: np.ndarray,
        downsampling_steps: int,
        downsampled_data_group: zarr.hierarchy.Group,
        value_to_segment_id_dict_for_specific_lattice_id: Dict
        ):
        '''
        Take original segmentation data, do all downsampling levels, create zarr datasets for each
        '''
        # table with just singletons, e.g. "104": {104}, "94" :{94}
        initial_set_table = SegmentationSetTable(original_data, value_to_segment_id_dict_for_specific_lattice_id)
        
        # to make it uniform int32 with other level grids
        original_data = original_data.astype(np.int32)

        # for now contains just x1 downsampling lvl dict, in loop new dicts for new levels are appended
        levels = [
            DownsamplingLevelDict({'ratio': 1, 'grid': original_data, 'set_table': initial_set_table})
            ]
        for i in range(downsampling_steps):
            current_set_table = SegmentationSetTable(original_data, value_to_segment_id_dict_for_specific_lattice_id)
            # on first iteration (i.e. when doing x2 downsampling), it takes original_data and initial_set_table with set of singletons 
            levels.append(self.__downsample_categorical_data_using_category_sets(levels[i], current_set_table))

        # store levels list in zarr structure (can be separate function)
        self.__store_downsampling_levels_in_zarr_structure(levels, downsampled_data_group)

    def __store_downsampling_levels_in_zarr_structure(self, levels_list: List[DownsamplingLevelDict], downsampled_data_group: zarr.hierarchy.Group):
        for level_dict in levels_list:
            grid = level_dict.get_grid()
            table = level_dict.get_set_table()
            ratio = level_dict.get_ratio()

            new_level_group: zarr.hierarchy.Group = downsampled_data_group.create_group(str(ratio))
            grid_arr = new_level_group.create_dataset(
                data=grid,
                name='grid',
                shape=grid.shape,
                dtype=grid.dtype,
                # # TODO: figure out how to determine optimal chunk size depending on the data
                chunks=(25, 25, 25)
            )
            
            table_obj_arr = new_level_group.create_dataset(
                # be careful here, encoding JSON, sets need to be converted to lists
                name='set_table',
                # MsgPack leads to bug/error: int is not allowed for map key when strict_map_key=True
                dtype=object,
                object_codec=numcodecs.JSON(),
                shape=1
            )

            table_obj_arr[...] = [table.get_serializable_repr()]

    def __downsample_categorical_data_using_category_sets(self, previous_level_dict: DownsamplingLevelDict, current_set_table: SegmentationSetTable) -> DownsamplingLevelDict:
        '''
        Downsample data returning a dict for that level containing new grid and a set table for that level
        '''
        previous_level_grid: np.ndarray = previous_level_dict.get_grid()
        previous_level_set_table: SegmentationSetTable = previous_level_dict.get_set_table()
        current_level_grid: np.ndarray = create_x2_downsampled_grid(previous_level_grid.shape, np.nan)

        # Select block
        # The following will not work for e.g. 5**3 grid, as block size = 2,2,2
        # blocks: np.ndarray = view_as_blocks(previous_level_grid, (2, 2, 2))
        # instead, get target voxels, e.g. for 1st block it is *0,0,0) voxel
        target_voxels_coords = np.array(extract_target_voxels_coords(previous_level_grid.shape))
        origin_coords = np.array([0, 0, 0])
        max_coords = np.subtract(previous_level_grid.shape, (1, 1, 1))
        # loop over voxels, c = coords of a single voxel
        for start_coords in target_voxels_coords:
            # end coords for start_coords 0,0,0 are 2,2,2
            # (it will actually select from 0,0,0 to 1,1,1 as slicing end index is non-inclusive)
            end_coords = start_coords + 2
            if (end_coords < origin_coords).any():
                end_coords = np.fmax(end_coords, origin_coords)
            if (end_coords > max_coords).any():
                end_coords = np.fmin(end_coords, max_coords)
            
            block: np.ndarray = previous_level_grid[
                start_coords[0] : end_coords[0],
                start_coords[1] : end_coords[1],
                start_coords[2] : end_coords[2]
            ]

            new_id: int = self.__downsample_2x2x2_categorical_block(block, current_set_table, previous_level_set_table)
            # putting that id in the location of new grid corresponding to that block
            current_level_grid[
                round(start_coords[0] / 2),
                round(start_coords[1] / 2),
                round(start_coords[2] / 2)
            ] = new_id
        
        # need to check before conversion to int as in int grid nans => some guge number
        assert np.isnan(current_level_grid).any() == False, f'Segmentation grid contain NAN values'

        current_level_grid = current_level_grid.astype(np.int32)
        # write grid into 'grid' key of new level dict
        # add current level set table to new level dict
        new_dict = DownsamplingLevelDict({
            'ratio': round(previous_level_dict.get_ratio() * 2),
            'grid': current_level_grid,
            'set_table': current_set_table
            })
        # and return that dict (will have a new grid and a new set table)  
        return new_dict
        

    def __downsample_2x2x2_categorical_block(self, block: np.ndarray, current_table: SegmentationSetTable, previous_table: SegmentationSetTable) -> int:
        potentially_new_category: Set = self.__compute_union(block, previous_table)
        category_id: int = current_table.resolve_category(potentially_new_category)
        return category_id


    def __compute_union(self, block: np.ndarray, previous_table: SegmentationSetTable) -> Set:
        # in general, where x y z are sets
        # result = x.union(y, z) 
        block_values: Tuple = tuple(block.flatten())
        categories: Tuple = previous_table.get_categories(block_values)
        union: Set = set().union(*categories)
        return union

    def __create_downsampling(self, original_data, rate, downsampled_data_group, isCategorical=False):
        '''Deprecated. Creates zarr array (dataset) filled with downsampled data'''
        # now this function is just for volume data dwnsmpling

        # not used as we switch to category-set-downsampling
        # if isCategorical:
        #     downsampled_data = self.__downsample_categorical_data(original_data, rate)
        # else:
        #     downsampled_data = self.__downsample_numerical_data(original_data, rate)
        
        downsampled_data = self.__downsample_numerical_data(original_data, rate)

        zarr_arr = downsampled_data_group.create_dataset(
            str(rate),
            shape=downsampled_data.shape,
            dtype=downsampled_data.dtype,
            # TODO: figure out how to determine optimal chunk size depending on the data
            chunks=(50, 50, 50)
            )
        zarr_arr[...] = downsampled_data

    def __hdf5_to_zarr(self, file_path: Path):
        '''
        Creates temp zarr structure mirroring that of hdf5
        '''
        self.temp_zarr_structure_path = self.temp_root_path / file_path.stem
        store: zarr.storage.DirectoryStore = zarr.DirectoryStore(str(self.temp_zarr_structure_path))
        # directory store does not need to be closed, zip does

        hdf5_file: h5py.File = h5py.File(file_path, mode='r')
        hdf5_file.visititems(self.__visitor_function)
        hdf5_file.close()
    
    def __initialize_empty_zarr_structure(self, volume_file_path: Path):
        '''
        Creates EMPTY temp zarr structure for the case when just volume file is provided
        '''
        self.temp_zarr_structure_path = self.temp_root_path / volume_file_path.stem
        store: zarr.storage.DirectoryStore = zarr.DirectoryStore(str(self.temp_zarr_structure_path))

    def __open_hdf5_as_segmentation_object(self, file_path: Path) -> SFFSegmentation:
        return SFFSegmentation.from_file(str(file_path.resolve()))

    def __visitor_function(self, name: str, node: h5py.Dataset) -> None:
        '''
        Helper function used to create zarr hierarchy based on hdf5 hierarchy from sff file
        Takes nodes one by one and depending of their nature (group/object dataset/non-object dataset)
        creates the corresponding zarr hierarchy element (group/array)
        '''
        # input hdf5 file may be too large for memory, so we save it in temp storage
        node_name = node.name[1:]
        if isinstance(node, h5py.Dataset):
            # for text-based fields, including lattice data (as it is b64 encoded zlib-zipped sequence)
            if node.dtype == 'object':
                data = [node[()]]
                arr = zarr.array(data, dtype=node.dtype, object_codec=numcodecs.MsgPack())
                zarr.save_array(self.temp_zarr_structure_path / node_name, arr, object_codec=numcodecs.MsgPack())
            else:
                arr = zarr.open_array(self.temp_zarr_structure_path / node_name, mode='w', shape=node.shape, dtype=node.dtype)
                arr[...] = node[()]
        else:
            # node is a group
            zarr.open_group(self.temp_zarr_structure_path / node_name, mode='w')

    def read_and_normalize_volume_map(self, volume_file_path: Path) -> np.ndarray:
        map_object = self.__read_volume_map_to_object(volume_file_path)
        normalized_axis_map_object = self.__normalize_axis_order(map_object)
        arr = self.__read_volume_data(normalized_axis_map_object)
        return arr

    def generate_kernel_3d_arr(self, pattern: List[int]) -> np.ndarray:
        '''
        Generates conv kernel based on pattern provided (e.g. [1,4,6,4,1]).
        https://stackoverflow.com/questions/71739757/generate-3d-numpy-array-based-on-provided-pattern/71742892#71742892
        '''
        pattern = pattern[0:3]
        x = np.array(pattern[-1]).reshape([1,1,1])
        for p in reversed(pattern[:-1]):
            x = np.pad(x, mode='constant', constant_values=p, pad_width=1)
        
        k = (1/x.sum()) * x
        # print(f'Kernel generated (further divided by sum): {x}')
        return k