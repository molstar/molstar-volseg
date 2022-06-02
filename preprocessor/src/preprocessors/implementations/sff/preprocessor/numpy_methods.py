import numpy as np


def chunk_numpy_arr(arr, chunk_size):
    return np.split(arr, np.arange(chunk_size, len(arr), chunk_size))