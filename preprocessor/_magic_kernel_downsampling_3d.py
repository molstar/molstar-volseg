from itertools import product
from typing import Tuple
import numpy as np
from math import ceil

def extract_target_voxels_coords(arr_shape: Tuple[int, int, int]):
    '''
    Takes 3D arr shape (X, Y, Z;), calculates max_grid_coords (-1 from each dimension)
    and returns coords of target voxels (every other in all three dimensions)
    that will be the centers of 5x5 boxes on which magic kernel is applied
    '''
    max_grid_coords = tuple(np.subtract(arr_shape, (1, 1, 1)))

    max_x = list(range(0, max_grid_coords[0] + 1, 2))
    max_y = list(range(0, max_grid_coords[1] + 1, 2))
    max_z = list(range(0, max_grid_coords[2] + 1, 2))
    
    lst = [max_x, max_y, max_z]
    permutations = product(*lst)
    # TODO: assert permutations == grid x/2 y/2 z/2
    return tuple(permutations)

def get_voxel_coords_at_radius(target_voxel_coords: Tuple[int, int, int], radius: int, arr_shape: Tuple[int, int, int]):
    '''
    Takes coords of a single target voxel and radius (e.g. 1 for inner, 2 for outer layer)
    and returns a list/arr of coords of voxels in surrounding depth layer according to radius
    '''
    # adapted with changes from: https://stackoverflow.com/a/34908879
    p = np.array(target_voxel_coords)
    ndim = len(p)
    # indices range for offsets for all layers (e.g. [-2, -1, 0, 1, 2])
    offset_idx_range_all_layers = _compute_offset_indices_from_radius(radius)
    # indices range for offsets for just inner layers (e.g. [-1, 0, 1])
    offset_idx_range_inner_layers = _compute_offset_indices_from_radius(radius - 1)

    # arr of all possible offsets if we select all layers (not just surface)
    offsets_all_layers = np.array(tuple(product(offset_idx_range_all_layers, repeat=ndim)))
    # arr of all possible offsets if we select just inner layers (except surface)
    offsets_inner_layers = np.array(tuple(product(offset_idx_range_inner_layers, repeat=ndim)))
    # arr of offsets corresponding to just surface layer (what is actually required)
    offsets_surface_layer = _setdiff2d_set(offsets_all_layers, offsets_inner_layers)
    
    # TODO: assert if length of offsets_surface is equal to len offsets minus len offsets_inside
    
    # coords of voxels at given radius
    voxels_at_radius = p + offsets_surface_layer

    # Checks if (some, e.g. just x=-2) coords of some voxels are out of boundaries
    # and replaces them with the corresponding coord of the boundary (origin or max_grid_coords) 
    origin = np.array([0, 0, 0])
    max_grid_coords = np.subtract(arr_shape, (1, 1, 1))
    # TODO: if possible - optimize later on (is it possible without looping?)
    # some np.all or whatever or
    # e.g. https://stackoverflow.com/questions/42150110/comparing-subarrays-in-numpy
    for v in voxels_at_radius:
        if (v < origin).any():
            voxels_at_radius = np.fmax(voxels_at_radius, origin)
        if (v > max_grid_coords).any():
            voxels_at_radius = np.fmin(voxels_at_radius, max_grid_coords)
    
    # in roder to use it for indexing 3D array it needs to be a list of tuples, not np array
    voxels_at_radius = list(map(tuple, voxels_at_radius))
    return voxels_at_radius

def compute_downsampled_voxel_value(arr: np.ndarray,
            kernel: Tuple[int, int, int, int, int],
            voxel_coords: Tuple[int, int, int],
            inner_layer_voxel_coords: Tuple[int, int, int],
            outer_layer_voxel_coords: Tuple[int, int, int]) -> float:
            # Kernel should be symmetric!!! e.g. 1, 4, 6, 4, 1, as
            # there is no distinction inside inner or outer layer

    # TODO: assert to check if kernel symmetric
    k = kernel
    target_voxel_value = arr[voxel_coords]
    inner_layer_voxel_values = np.array([arr[i] for i in inner_layer_voxel_coords])
    outer_layer_voxel_values = np.array([arr[i] for i in outer_layer_voxel_coords])
    # print(inner_layer_voxel_values)
    # print(outer_layer_voxel_values)
    # print(target_voxel_value)
    values_sum = k[2] * target_voxel_value + k[1] * inner_layer_voxel_values.sum() + k[0] * outer_layer_voxel_values.sum()
    new_value = values_sum / sum(k)
    # print(values_sum)
    # print(new_value)
    return new_value


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
    
    
def downsample_using_magic_kernel(arr: np.ndarray, kernel: Tuple[int, int, int, int, int]) -> np.ndarray:
    # empty 3D arr with /2 dimensions compared to original 3D arr
    downsampled_arr = np.full([
        ceil(arr.shape[0] / 2),
        ceil(arr.shape[1] / 2),
        ceil(arr.shape[2] / 2)
    ], np.nan)

    target_voxels_coords = extract_target_voxels_coords(arr.shape)
    for voxel_coords in target_voxels_coords:
        inner_layer_voxel_coords = get_voxel_coords_at_radius(voxel_coords, 1, arr.shape)
        outer_layer_voxel_coords = get_voxel_coords_at_radius(voxel_coords, 2, arr.shape)
        downsampled_voxel_value = compute_downsampled_voxel_value(
            arr,
            kernel,
            voxel_coords,
            inner_layer_voxel_coords,
            outer_layer_voxel_coords
        )
        new_x = int(voxel_coords[0] / 2)
        new_y = int(voxel_coords[1] / 2)
        new_z = int(voxel_coords[2] / 2)
        downsampled_arr[new_x][new_y][new_z] = downsampled_voxel_value

    return downsampled_arr

if __name__ == '__main__':
    # __testing()
    __testing_with_dummy_arr()