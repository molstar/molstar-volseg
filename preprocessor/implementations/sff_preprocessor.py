

import base64
from pathlib import Path
from typing import Tuple
import zlib
import zarr
import numcodecs
import h5py
import numpy as np
from preprocessor.interface.i_data_preprocessor import IDataPreprocessor
from preprocessor.preprocessor import DOWNSAMPLING_STEPS


class SFFPreprocessor(IDataPreprocessor):
    def __init__(self):
        # path to root of temporary storage for zarr hierarchy
        self.temp_root_path = Path(__file__).parents[0] / 'temp_zarr_hierarchy_storage'
        # path to temp storage for that entry (segmentation)
        self.temp_zarr_structure_path = None

    def preprocess(self, file_path: Path):
        '''
        Returns processed data (zarr structure) that will be stored using db.store
        '''
        self.__hdf5_to_zarr(file_path)
        # Re-create zarr hierarchy from opened store
        store: zarr.storage.DirectoryStore = zarr.DirectoryStore(self.temp_zarr_structure_path, mode='r')
        zarr_structure: zarr.hierarchy.group = zarr.group(store=store)
        for gr_name, gr in zarr_structure.lattice_list.groups():
            self.__create_downsamplings(gr)

        # TODO: empty the temp storage for zarr hierarchies (maybe that file will be converted again!) 

    def __lattice_data_to_np_arr(self, data: str, dtype: str, arr_shape: Tuple[int, int, int]) -> np.ndarray:
        '''
        Converts lattice data to np array.
        Under the hood, decodes lattice data into zlib-zipped data, decompress it to bytes,
        and converts to np arr based on dtype (sff mode) and shape (sff size)
        '''
        decoded_data = base64.b64decode(data)
        byteseq = zlib.decompress(decoded_data)
        return np.frombuffer(byteseq, dtype=dtype).reshape(arr_shape)

    def __downsample_data(self, arr: np.ndarray, rate) -> np.ndarray:
        '''Returns downsampled (e.g. every other value) np array'''
        # return block_reduce(arr, block_size=(2, 2, 2), func=np.max)
        pass
    
    def __create_downsamplings(self, gr):
        # TODO create x1 "down"sampling too
        data = self.__lattice_data_to_np_arr(
            gr.data[0],
            gr.mode[0],
            (gr.size.cols[...], gr.size.rows[...], gr.size.sections[...]))

        downsampled_data_group = gr.create_group('downsampled_data')
        # iteratively downsample data, create arr for each dwns. level and store data 
        ratios = 2 ** np.arange(1, DOWNSAMPLING_STEPS + 1)
        for rate in ratios:
            self.__create_downsampling(data, gr, rate, downsampled_data_group)
        # TODO: figure out compression/filters: b64 encoded zlib-zipped .data is just 8 bytes
        # downsamplings sizes in raw uncompressed state are much bigger 
        # TODO: figure out what to do with chunks - currently they are not used

    def __create_downsampling(self, original_data, rate, downsampled_data_group):
        '''Creates zarr array (dataset) filled with downsampled data'''
        downsampled_data = self.__downsample_data(original_data, rate)
        zarr_arr = downsampled_data_group.create_dataset(
            str(rate),
            shape=downsampled_data.shape,
            dtype=downsampled_data.dtype)
        zarr_arr[...] = downsampled_data

    def __hdf5_to_zarr(self, file_path: Path):
        '''
        Returns zarr structure mirroring that of hdf5
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
    

