

import base64
import json
import gemmi
from pathlib import Path
from typing import Dict, Tuple
import zlib
import zarr
import numcodecs
import h5py
import numpy as np
from preprocessor.interface.i_data_preprocessor import IDataPreprocessor
# TODO: figure out how to specify N of downsamplings (x2, x4, etc.) in a better way
from preprocessor._deprecated_preprocessor import DOWNSAMPLING_STEPS
from skimage.measure import block_reduce

VOLUME_DATA_GROUPNAME = '_segmentation_data'
SEGMENTATION_DATA_GROUPNAME = '_segmentation_data'
METADATA_FILENAME = 'metadata.json'

class SFFPreprocessor(IDataPreprocessor):
    def __init__(self):
        # path to root of temporary storage for zarr hierarchy
        self.temp_root_path = Path(__file__).parents[0] / 'temp_zarr_hierarchy_storage'
        # path to temp storage for that entry (segmentation)
        self.temp_zarr_structure_path = None

    def preprocess(self, file_path: Path, volume_file_path: Path):
        '''
        Returns path to temporary zarr structure that will be stored using db.store
        '''
        self.__hdf5_to_zarr(file_path)
        # Re-create zarr hierarchy from opened store
        store: zarr.storage.DirectoryStore = zarr.DirectoryStore(self.temp_zarr_structure_path, mode='r')
        zarr_structure: zarr.hierarchy.group = zarr.group(store=store)
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
            self.__create_downsamplings(segm_arr, lattice_gr)
        
        volume_arr = self.__read_volume_data(volume_file_path)
        self.__create_downsamplings(volume_arr, volume_data_gr)
        
        metadata = self.__extract_metadata(zarr_structure)
        self.__temp_save_metadata(metadata, self.temp_zarr_structure_path)

        store.close()
        return self.temp_zarr_structure_path
        # TODO: empty the temp storage for zarr hierarchies here or in db.store (maybe that file will be converted again!) 

    def __extract_metadata(zarr_structure) -> Dict:
        # just sample fields for now
        root = zarr_structure
        lattice_dict = {}
        for gr_name, gr in root[SEGMENTATION_DATA_GROUPNAME]:
            # each key is lattice id
            lattice_dict[f'lattice_{gr_name}'] = sorted(gr.array_keys())

        return {
            'details': root.details[...][0],
            'volume_data_downsamplings': sorted(root[VOLUME_DATA_GROUPNAME].array_keys()),
            'segmentation_data_downsamplings': lattice_dict,
        }

    def __temp_save_metadata(metadata: Dict, temp_dir_path: Path) -> None:
        with (temp_dir_path / METADATA_FILENAME).open('w') as fp:
            json.dump(metadata, fp)

    def __read_volume_data(self, file_path) -> np.ndarray:
        # may not need to add .resolve(), with resolve it returns abs path
        m = gemmi.read_ccp4_map(str(file_path.resolve()))
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
            dtype=downsampled_data.dtype)
        zarr_arr[...] = downsampled_data

    def __hdf5_to_zarr(self, file_path: Path):
        '''
        Creates temp zarr structure mirroring that of hdf5
        '''
        self.temp_zarr_structure_path = self.temp_root_path / file_path.stem
        store: zarr.storage.DirectoryStore = zarr.DirectoryStore(self.temp_zarr_structure_path, mode='r')
        # may not need to be closed, but just in case

        hdf5_file: h5py._hl.files.File = h5py.File(file_path, mode='r')
        hdf5_file.visititems(self.__visitor_function)
        hdf5_file.close()
        
        store.close()

    def __visitor_function(self, name: str, node: h5py._hl.dataset.Dataset) -> None:
        '''
        Helper function used to create zarr hierarchy based on hdf5 hierarchy from sff file
        Takes nodes one by one and depending of their nature (group/object dataset/non-object dataset)
        creates the corresponding zarr hierarchy element (group/array)
        '''
        # TODO: may not work as it is a method, not a function. Check?
        # input hdf5 file may be too large for memory, so we save it in temp storage
        if isinstance(node, h5py.Dataset):
            # for text-based fields, including lattice data (as it is b64 encoded zlib-zipped sequence)
            if node.dtype == 'object':
                data = [node[()]]
                arr = zarr.array(data, dtype=node.dtype, object_codec=numcodecs.MsgPack())
                zarr.save_array(self.temp_zarr_structure_path / node.name, arr, object_codec=numcodecs.MsgPack())
            else:
                arr = zarr.open_array(self.temp_zarr_structure_path / node.name, mode='w', shape=node.shape, dtype=node.dtype)
                arr[...] = node[()]
        else:
            # node is a group
            zarr.open_group(self.temp_zarr_structure_path / node.name, mode='w')
    

