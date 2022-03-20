from itertools import product
from typing import Tuple
import numpy as np
# TODO: address overflow (see todo somewhere below)
def extract_target_voxels_coords():
    '''
    Takes 3d arr and extract coords of target voxels (every other in all three dimensions)
    '''
    # repeat - n of dimensions, list = list of values of group for that permutation
    # TODO: determine lst based on grid dimensions
    lst = [0, 2, 4]
    permutations = product(lst, repeat=3)
    # TODO: assert permutations == grid x/2 y/2 z/2
    return tuple(permutations)

def get_surrounding_voxels_coords(target_voxel_coords: Tuple[int, int, int], radius: int):
    '''
    Takes coords of a single target voxel and radius (e.g. 1 for inner, 2 for outer layer)
    and returns a list/arr of coords of voxels in surrounding depth layer according to radius
    '''
    # adapted with changes from: https://stackoverflow.com/a/34908879
    # TODO: shape=None overflow - do we need it?
    p = np.array(target_voxel_coords)
    ndim = len(p)
    # indices range for offsets for all layers (e.g. [-2, -1, 0, 1, 2])
    offset_idx_range_all_layers = _compute_offset_indices_from_radius(radius)
    # indices range for offsets for just inner layers (e.g. [-1, 0, 1])
    offset_idx_range_inner_layers = _compute_offset_indices_from_radius(radius - 1)

    # arr of all possible offsets if we select all layers (not just surface)
    offsets_all_layers = np.array(tuple(product(offset_idx_range_all_layers, repeat=3)))
    # arr of all possible offsets if we select just inner layers (except surface)
    offsets_inner_layers = np.array(tuple(product(offset_idx_range_inner_layers, repeat=3)))
    # arr of offsets corresponding to just surface layer (what is actually required)
    offsets_surface_layer = _setdiff2d_set(offsets_all_layers, offsets_inner_layers)
    
    # TODO: assert if length of offsets_surface is equal to len offsets minus len offsets_inside
    
    neighbours = p + offsets_surface_layer
    return neighbours

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

r = get_surrounding_voxels_coords((3, 3, 3), 1)
print(r)
print(len(r))