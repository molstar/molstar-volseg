import base64
import json
import gemmi
from pathlib import Path
from typing import Dict, Set, Tuple
import zlib
import zarr
import numcodecs
import h5py
import numpy as np
import decimal
from decimal import Decimal
from preprocessor.interface.i_data_preprocessor import IDataPreprocessor
# TODO: figure out how to specify N of downsamplings (x2, x4, etc.) in a better way
from skimage.measure import block_reduce
import math
from preprocessor._magic_kernel_downsampling_3d import downsample_using_magic_kernel, get_voxel_coords_at_radius
from skimage.util import view_as_blocks

VOLUME_DATA_GROUPNAME = '_volume_data'
SEGMENTATION_DATA_GROUPNAME = '_segmentation_data'
METADATA_FILENAME = 'metadata.json'
MIN_GRID_SIZE = 100 **3
DOWNSAMPLING_KERNEL = (1, 4, 6, 4, 1)


def open_zarr_structure_from_path(path: Path) -> zarr.hierarchy.Group:
    store: zarr.storage.DirectoryStore = zarr.DirectoryStore(str(path))
    # Re-create zarr hierarchy from opened store
    root: zarr.hierarchy.group = zarr.group(store=store)
    return root

class SegmentationSetTable:
    def __init__(self, lattice):
        self.entries: Dict = self.__convert_lattice_to_dict_of_sets(lattice)
        # figure out how to create entries upon initialization given the original segm lattice
    
    def __convert_lattice_to_dict_of_sets(self, lattice: np.ndarray) -> Dict:
        '''
        Converts original latice to dict of singletons
        '''
        unique_values: np.ndarray = np.unique(lattice)
        z = zip(unique_values, unique_values)
        return dict(z)

    def get_categories(self, ids: Tuple) -> Tuple:
        '''
        Returns sets from the dict of sets (entries) based on provided IDs
        '''
        return tuple([self.entries[i] for i in ids])

    def __find_category(self, target_category: Set) -> Union[int, None]:
        '''
        Looks up a category (set) in entries dict, returns its id or None if not found
        '''
        # TODO: check if dict has unique categories indeed!
        for id, category in self.entries.iteritems():
            if category == target_category:
                return id
        return None

    def __add_category(self, target_category: Set) -> int:
        '''
        Adds new category to entries and returns its id
        '''
        new_id = max(self.entries.keys()) + 1
        self.entries[new_id] = target_category
        return new_id

    def resolve_category(self, target_category: Set):
        '''
        Looks up a category (set) in entries dict, returns its id
        If not found, adds new category to entries and returns its id
        '''
        if id := self.__find_category(target_category):
            return id
        else:
            return self.__add_category(target_category)



class SFFPreprocessor(IDataPreprocessor):
    def __init__(self):
        # path to root of temporary storage for zarr hierarchy
        self.temp_root_path = Path(__file__).parents[1] / 'temp_zarr_hierarchy_storage'
        # path to temp storage for that entry (segmentation)
        self.temp_zarr_structure_path = None

    def preprocess(self, segm_file_path: Path, volume_file_path: Path):
        '''
        Returns path to temporary zarr structure that will be stored permanently using db.store
        '''
        self.__hdf5_to_zarr(segm_file_path)
        # Re-create zarr hierarchy
        zarr_structure: zarr.hierarchy.group = open_zarr_structure_from_path(
            self.temp_zarr_structure_path)
        
        # read map
        map_object = self.__read_volume_map_to_object(volume_file_path)
        normalized_axis_map_object = self.__normalize_axis_order(map_object)
        
        self.__process_segmentation_data(zarr_structure)
        self.__process_volume_data(zarr_structure, normalized_axis_map_object)
        
        metadata = self.__extract_metadata(zarr_structure, normalized_axis_map_object)
        self.__temp_save_metadata(metadata, self.temp_zarr_structure_path)

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

    def __process_volume_data(self, zarr_structure: zarr.hierarchy.group, map_object: gemmi.Ccp4Map):
        '''
        Takes read map object, extracts volume data, downsamples it, stores to zarr_structure
        '''
        volume_data_gr: zarr.hierarchy.group = zarr_structure.create_group(VOLUME_DATA_GROUPNAME)        
        volume_arr = self.__read_volume_data(map_object)
        volume_downsampling_steps = self.__compute_number_of_downsampling_steps(
            MIN_GRID_SIZE,
            input_grid_size=math.prod(volume_arr.shape)
        )
        self.__create_downsamplings(
            volume_arr,
            volume_data_gr,
            isCategorical=False,
            downsampling_steps = volume_downsampling_steps
        )

    def __process_segmentation_data(self, zarr_structure: zarr.hierarchy.group) -> None:
        '''
        Extracts segmentation data from lattice, downsamples it, stores to zarr structure
        '''
        segm_data_gr: zarr.hierarchy.group = zarr_structure.create_group(SEGMENTATION_DATA_GROUPNAME)
        
        for gr_name, gr in zarr_structure.lattice_list.groups():
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
            self.__create_downsamplings(
                segm_arr,
                lattice_gr,
                isCategorical=True,
                downsampling_steps = segmentation_downsampling_steps
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

    def __extract_metadata(self, zarr_structure: zarr.hierarchy.group, map_object) -> Dict:
        root = zarr_structure
        volume_downsamplings = sorted(root[VOLUME_DATA_GROUPNAME].array_keys())

        lattice_dict = {}
        lattice_ids = []
        for gr_name, gr in root[SEGMENTATION_DATA_GROUPNAME].groups():
            # each key is lattice id
            lattice_id = int(gr_name)
            lattice_dict[lattice_id] = sorted(gr.array_keys())
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
        grid_dimensions: Tuple[int, int, int] = (d['NC'], d['NR'], d['NS'])

        return {
            'details': root.details[...][0].decode('utf-8'),
            'volume_downsamplings': volume_downsamplings,
            'segmentation_lattice_ids': lattice_ids,
            'segmentation_downsamplings': lattice_dict,
            # downsamplings have different voxel size so it is a dict
            'voxel_size': voxel_sizes_in_downsamplings,
            'origin': origin,
            'grid_dimensions': grid_dimensions,
        }

    def __temp_save_metadata(self, metadata: Dict, temp_dir_path: Path) -> None:
        with (temp_dir_path / METADATA_FILENAME).open('w') as fp:
            json.dump(metadata, fp)

    def __read_volume_data(self, m) -> np.ndarray:
        '''
        Takes read map object (axis normalized upfront) and returns numpy arr with volume data
        '''
        # TODO: can be dask array to save memory?
        return np.array(m.grid)

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
        '''Returns downsampled (mean) np array'''
        if rate == 1:
            return arr
        # return block_reduce(arr, block_size=(rate, rate, rate), func=np.mean)
        # TODO:
        return downsample_using_magic_kernel(arr, DOWNSAMPLING_KERNEL)

    def __create_downsamplings(self, data: np.ndarray, downsampled_data_group: zarr.hierarchy.group, isCategorical: bool = False, downsampling_steps: int = 1):
        # iteratively downsample data, create arr for each dwns. level and store data 
        ratios = 2 ** np.arange(0, downsampling_steps + 1)
        if isCategorical:
            # separate function as we need to keep info from previous dwns lvl
            self.__create_category_set_downsamplings(data, downsampling_steps, downsampled_data_group)
        else:
            for rate in ratios:
                self.__create_downsampling(data, rate, downsampled_data_group, isCategorical)
        # TODO: figure out compression/filters: b64 encoded zlib-zipped .data is just 8 bytes
        # downsamplings sizes in raw uncompressed state are much bigger 
        # TODO: figure out what to do with chunks - currently they are not used

    def __create_category_set_downsamplings(self, original_data: np.ndarray, downsampling_steps: int, downsampled_data_group):
        '''
        Take original segmentation data, do all downsampling levels, create zarr datasets for each
        '''
        # table with just singletons, e.g. "104": {104}, "94" :{94}
        initial_set_table = SegmentationSetTable(original_data)
        
        levels = [{'grid': original_data, 'set_table': initial_set_table}]
        for i in range(downsampling_steps):
            current_set_table = SegmentationSetTable(original_data)
            # on first iteration (i.e. when doing x2 downsampling), it takes original_data and initial_set_table with set of singletons 
            levels.append(self.__downsample_categorical_data_using_category_sets(levels[i], current_set_table))

        # TODO: store levels list in zarr structure (can be separate function)

    def __downsample_categorical_data_using_category_sets(self, previous_level_dict: Dict, current_set_table: SegmentationSetTable) -> Dict:
        '''
        Downsample data returning a dict for that level containing new grid and a set table for that level
        '''
        previous_level_grid: np.ndarray = previous_level_dict['grid']
        previous_level_set_table: SegmentationSetTable = previous_level_dict['set_table']

        # TODO: figure out how to select block
        # this will not work for e.g. 5**3 grid, as block size = 2,2,2
        # blocks: np.ndarray = view_as_blocks(previous_level_grid, (2, 2, 2))
        # TODO: for loop does not know the coordinates
        # get them?
        for block in blocks:
            id = self.__downsample_2x2x2_categorical_block(block, current_set_table, previous_level_set_table)
            # TODO: put that id in the location of new grid corresponding to that block
            # , and write it into 'grid' key of new level dict

        # TODO: add current level set table to new level dict
        # and return that dict (will have a new grid and a new set table)  


    def __downsample_2x2x2_categorical_block(self, block: np.ndarray, current_table: SegmentationSetTable, previous_table: SegmentationSetTable) -> int:
        potentially_new_category: Set = self.__compute_union(block, previous_table)
        id: int = current_table.resolve_category(potentially_new_category)
        return id


    def __compute_union(self, block: np.ndarray, previous_table: SegmentationSetTable) -> Set:
        # in general, where x y z are sets
        # result = x.union(y, z) 
        block_values: Tuple = tuple(block.flatten())
        categories: Tuple = previous_table.get_categories(block_values)
        union: Set = set().union(*categories)
        return union

    def __create_downsampling(self, original_data, rate, downsampled_data_group, isCategorical=False):
        '''Creates zarr array (dataset) filled with downsampled data'''
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



# def __downsample_using_magic_kernel(arr: np.ndarray) -> np.ndarray:
#     pass
