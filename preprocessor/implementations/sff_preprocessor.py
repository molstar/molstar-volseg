

import base64
from pathlib import Path
import zlib
import zarr
import numcodecs
import h5py
import numpy as np
from preprocessor.interface.i_data_preprocessor import IDataPreprocessor


class SFFPreprocessor(IDataPreprocessor):
    def preprocess(self, file_path: Path):
        pass

    def __decode_lattice_data(self, data):
        '''Decodes lattice data into just zlib-zipped data'''
        return base64.b64decode(data)

    def __decompress_lattice_data(self, decoded_data):
        '''Decompresses lattice data to bytes'''
        return zlib.decompress(decoded_data)

    def __convert_bytes_to_arr(self, decompressed_bytes, dtype, arr_shape):
        '''Converts decompressed lattice date (bytes) into np arr based on dtype (sff mode) and shape (sff size)'''
        return np.frombuffer(decompressed_bytes, dtype=dtype).reshape(arr_shape)

    def __downsample_arr(self, arr):
        '''Returns downsampled (e.g. every other value) array'''
        pass

    def __visitor_function(self, name, node: h5py._hl.dataset.Dataset):
        '''
        Helper function used to create zarr hierarchy based on hdf5 hierarchy from sff file,
        with addtional items (e.g. downsampled_data group, possibly metadata)
        '''
        # TODO: uncomment and rework code (taken from preprocessor.py) so that it works in class
        # emdb_seg_id = hdf5_file.filename.split('/')[-1].split('.')[0]
        # root_path = PATH_TO_OUTPUT_DIR + emdb_seg_id
        # if isinstance(node, h5py.Dataset):
        #     # for text-based fields, including lattice data (as it is b64 encoded zlib-zipped sequence)
        #     if node.dtype == 'object':
        #         data = [node[()]]
        #         arr = zarr.array(data, dtype=node.dtype, object_codec=numcodecs.MsgPack())
        #         zarr.save_array(root_path + node.name, arr, object_codec=numcodecs.MsgPack())
        #     else:
        #         arr = zarr.open_array(root_path + node.name, mode='w', shape=node.shape, dtype=node.dtype)
        #         arr[...] = node[()]
        # else:
        #     # node is a group
        #     # TODO: fix paths
        #     zarr.open_group(root_path + node.name, mode='w')

    

