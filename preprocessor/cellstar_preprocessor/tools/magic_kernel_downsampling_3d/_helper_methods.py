from typing import Tuple

import numpy as np


def compute_offset_indices_from_radius(radius: int):
    """
    Computes offset indices array based on radius, so that only the voxels of specific depth layer
    (e.g. nearest (1st layer), or next to nearest (2nd layer)) voxels can be selected downstream in the code
    """
    return list(range(-radius, radius + 1))


def setdiff2d_set(bigger_arr, smaller_arr):
    """
    Difference between two 2D arrays
    https://stackoverflow.com/a/66674679
    """
    set1 = set(map(tuple, bigger_arr))
    set2 = set(map(tuple, smaller_arr))
    return np.array(list(set1 - set2))


def generate_dummy_arr(shape: Tuple[int, int, int]) -> np.ndarray:
    np_arr = np.arange(shape[0] * shape[1] * shape[2]).reshape(
        (shape[0], shape[1], shape[2])
    )
    return np_arr
