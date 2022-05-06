from itertools import product
from typing import Tuple
import numpy as np
from math import ceil


def _compute_offset_indices_from_radius(radius: int):
    '''
    Computes offset indices array based on radius, so that only the voxels of specific depth layer
    (e.g. nearest (1st layer), or next to nearest (2nd layer)) voxels can be selected downstream in the code
    '''
    return list(range(-radius, radius + 1))

def _setdiff2d_set(bigger_arr, smaller_arr):
    '''
    Difference between two 2D arrays
    https://stackoverflow.com/a/66674679
    '''
    set1 = set(map(tuple, bigger_arr))
    set2 = set(map(tuple, smaller_arr))
    return np.array(list(set1 - set2))

def __generate_dummy_arr(shape: Tuple[int, int, int]) -> np.ndarray:
    np_arr = np.arange(shape[0] * shape[1] * shape[2]).reshape((shape[0], shape[1], shape[2]))
    return np_arr

def __testing():
    radius = 2
    max_dims = (10, 12, 14)

    lst_of_coords = [
        (0, 0, 0),
        (10, 12, 14),
        (0, 12, 0),
        (10, 0, 0)
    ]

    for coords in lst_of_coords:
        r = get_voxel_coords_at_radius(coords, radius, max_dims)
        print(r)
        print(len(r))

    lst_of_max_coords = [
        (4, 5, 4),
        (10, 12, 14),
        (2, 11, 2),
        (10, 4, 8)
    ]

    for coords in lst_of_max_coords:
        result = extract_target_voxels_coords(coords)
        print(f'For {coords} there are {len(result)} target voxels')
        print()

def __testing_with_dummy_arr():
    SHAPE = (10, 12, 14)
    KERNEL = (1, 4, 6, 4, 1)
    arr =__generate_dummy_arr(SHAPE)
    downsampled_arr = downsample_using_magic_kernel(arr, KERNEL)
    print(f'ORIGINAL ARR, SHAPE {arr.shape}')
    print(arr)
    print(f'DOWNSAMPLED ARR, SHAPE {downsampled_arr.shape}')
    print(downsampled_arr)
    
    


if __name__ == '__main__':
    # __testing()
    __testing_with_dummy_arr()