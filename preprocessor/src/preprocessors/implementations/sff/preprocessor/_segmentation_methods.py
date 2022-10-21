import base64
import logging
import zlib

import numpy as np

from preprocessor.src.preprocessors.implementations.sff.preprocessor.numpy_methods import decide_np_dtype


def lattice_data_to_np_arr(data: str, mode: str, endianness: str, arr_shape: tuple[int, int, int]) -> np.ndarray:
    '''
    Converts lattice data to np array.
    Under the hood, decodes lattice data into zlib-zipped data, decompress it to bytes,
    and converts to np arr based on dtype (sff mode), endianness and shape (sff size)
    '''
    try:
        decoded_data = base64.b64decode(data)
        byteseq = zlib.decompress(decoded_data)
        np_dtype = decide_np_dtype(mode=mode, endianness=endianness)
        arr = np.frombuffer(byteseq, dtype=np_dtype).reshape(arr_shape, order='C')
    except Exception as e:
        logging.error(e, stack_info=True, exc_info=True)
        raise e
    return arr

def decode_base64_data(data: str, mode: str, endianness: str):
    try:
        # TODO: decode any data, take into account endiannes
        decoded_data = base64.b64decode(data)
        np_dtype = decide_np_dtype(mode=mode, endianness=endianness)
        arr = np.frombuffer(decoded_data, dtype=np_dtype)
    except Exception as e:
        logging.error(e, stack_info=True, exc_info=True)
        raise e
    return arr

def map_value_to_segment_id(zarr_structure):
    '''
    Iterates over zarr structure and returns dict with
    keys=lattice_id, and for each lattice id => keys=grid values, values=segm ids
    '''
    root = zarr_structure
    d = {}
    for segment_name, segment in root.segment_list.groups():
        lat_id = int(segment.three_d_volume.lattice_id[...])
        value = int(segment.three_d_volume.value[...])
        segment_id = int(segment.id[...])
        if lat_id not in d:
            d[lat_id] = {}
        d[lat_id][value] = segment_id
    # print(d)
    return d
