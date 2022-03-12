

import base64
from importlib.machinery import PathFinder
import json
import gemmi
from pathlib import Path
from typing import Dict, Tuple
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

DOWNSAMPLING_STEPS = 4
VOLUME_DATA_GROUPNAME = '_volume_data'
SEGMENTATION_DATA_GROUPNAME = '_segmentation_data'
METADATA_FILENAME = 'metadata.json'

class SFFPreprocessor(IDataPreprocessor):
    def __init__(self):
        # path to root of temporary storage for zarr hierarchy
        self.temp_root_path = Path(__file__).parents[1] / 'temp_zarr_hierarchy_storage'
        # path to temp storage for that entry (segmentation)
        self.temp_zarr_structure_path = None

    def preprocess(self, segm_file_path: Path, volume_file_path: Path):
        '''
        Returns path to temporary zarr structure that will be stored using db.store
        '''
        self.__hdf5_to_zarr(segm_file_path)
        # Re-create zarr hierarchy
        store: zarr.storage.DirectoryStore = zarr.DirectoryStore(self.temp_zarr_structure_path)
        zarr_structure: zarr.hierarchy.group = zarr.group(store=store)
        # zarr_structure: zarr.hierarchy.group = zarr.open_group(store=self.temp_zarr_structure_path, mode='r')
        volume_data_gr: zarr.hierarchy.group = zarr_structure.create_group(VOLUME_DATA_GROUPNAME)
        segm_data_gr: zarr.hierarchy.group = zarr_structure.create_group(SEGMENTATION_DATA_GROUPNAME)
        
        for gr_name, gr in zarr_structure.lattice_list.groups():
            # TODO create x1 "down"sampling too
            segm_arr = self.__lattice_data_to_np_arr(
                gr.data[0],
                gr.mode[0],
                (gr.size.cols[...], gr.size.rows[...], gr.size.sections[...]))
            # specific lattice with specific id
            lattice_gr = segm_data_gr.create_group(gr_name)
            self.__create_downsamplings(segm_arr, lattice_gr, isCategorical=True)
        
        volume_arr = self.__read_volume_data(volume_file_path)
        self.__create_downsamplings(volume_arr, volume_data_gr, isCategorical=False)
        
        metadata = self.__extract_metadata(zarr_structure, volume_file_path)
        self.__temp_save_metadata(metadata, self.temp_zarr_structure_path)

        return self.temp_zarr_structure_path
        
    def __extract_metadata(self, zarr_structure, volume_file_path: Path) -> Dict:
        root = zarr_structure
        volume_downsamplings = sorted(root[VOLUME_DATA_GROUPNAME].array_keys())

        lattice_dict = {}
        lattice_ids = []
        for gr_name, gr in root[SEGMENTATION_DATA_GROUPNAME].groups():
            # each key is lattice id
            lattice_id = int(gr_name)
            lattice_dict[lattice_id] = sorted(gr.array_keys())
            lattice_ids.append(lattice_id)

        # read ccp4 map to gemmi.Ccp4Map 
        # https://www.ccpem.ac.uk/mrc_format/mrc2014.php
        # https://www.ccp4.ac.uk/html/maplib.html
        volume_map = gemmi.read_ccp4_map(str(volume_file_path.resolve()))
        m = volume_map
        # get voxel size based on CELLA and NX/NC, NY/NR, NZ/NS variables (words 1, 2, 3) in CCP4 file
        # may need to use MX, NY, MZ instead of N*s (words 8, 9, 10)
        ctx = decimal.getcontext()
        ctx.rounding = decimal.ROUND_CEILING

        cella_X = round(Decimal(m.header_float(11)), 1)
        cella_Y = round(Decimal(m.header_float(12)), 1)
        cella_Z = round(Decimal(m.header_float(13)), 1)
        nx = m.header_i32(1)
        ny = m.header_i32(2)
        nz = m.header_i32(3)
        nc_start = m.header_i32(5)
        nr_start = m.header_i32(6)
        ns_start = m.header_i32(7)
        original_voxel_size: Tuple[float, float, float] = (
            cella_X / nx,
            cella_Y / ny,
            cella_Z / nz
        )

        voxel_sizes_in_downsamplings: Dict = {}
        for rate in volume_downsamplings:
            voxel_sizes_in_downsamplings[rate] = tuple(
                [float(str(i * Decimal(rate))) for i in original_voxel_size]
            )

        # get origin of grid based on NC/NR/NSSTART variables (5, 6, 7) and original voxel size
        origin: Tuple[float, float, float] = (
            m.header_i32(5) * original_voxel_size[0],
            m.header_i32(6) * original_voxel_size[1],
            m.header_i32(7) * original_voxel_size[2],
        )
        # Converting to strings, then to floats to make it JSON serializable (decimals are not)
        origin = tuple([float(str(i)) for i in origin])

        # get grid dimensions based on NX/NC, NY/NR, NZ/NS variables (words 1, 2, 3) in CCP4 file
        grid_dimensions: Tuple[int, int, int] = (nx, ny, nz)

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

    def __read_volume_data(self, file_path) -> np.ndarray:
        # may not need to add .resolve(), with resolve it returns abs path
        m = gemmi.read_ccp4_map(str(file_path.resolve()))
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
        # TODO: if choosing between '0' and non-zero value, it should perhaps leave non-zero value
        return arr[::rate, ::rate, ::rate]
    
    def __downsample_numerical_data(self, arr: np.ndarray, rate: int) -> np.ndarray:
        '''Returns downsampled (mean) np array'''
        return block_reduce(arr, block_size=(rate, rate, rate), func=np.mean)

    def __create_downsamplings(self, data: np.ndarray, downsampled_data_group: zarr.hierarchy.group, isCategorical=False):
        # iteratively downsample data, create arr for each dwns. level and store data 
        ratios = 2 ** np.arange(1, DOWNSAMPLING_STEPS + 1)
        for rate in ratios:
            self.__create_downsampling(data, rate, downsampled_data_group, isCategorical)
        # TODO: figure out compression/filters: b64 encoded zlib-zipped .data is just 8 bytes
        # downsamplings sizes in raw uncompressed state are much bigger 
        # TODO: figure out what to do with chunks - currently they are not used

    def __create_downsampling(self, original_data, rate, downsampled_data_group, isCategorical=False):
        '''Creates zarr array (dataset) filled with downsampled data'''
        if isCategorical:
            downsampled_data = self.__downsample_categorical_data(original_data, rate)
        else:
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
        store: zarr.storage.DirectoryStore = zarr.DirectoryStore(self.temp_zarr_structure_path)
        # directory store does not need to be closed, zip does

        hdf5_file: h5py._hl.files.File = h5py.File(file_path, mode='r')
        hdf5_file.visititems(self.__visitor_function)
        hdf5_file.close()

    def __visitor_function(self, name: str, node: h5py._hl.dataset.Dataset) -> None:
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
    

