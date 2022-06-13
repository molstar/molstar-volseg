import numpy as np


def chunk_numpy_arr(arr: np.ndarray, chunk_size: int):
    lst = np.split(arr, np.arange(chunk_size, len(arr), chunk_size))
    return np.stack(lst, axis=0)

def decide_np_dtype(mode: str, endianness: str):
    '''decides np dtype based on mode (e.g. float32) and endianness (e.g. little) provided in SFF
    '''
    dt = np.dtype(mode)
    dt = dt.newbyteorder(endianness)
    return dt