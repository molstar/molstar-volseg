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

def get_voxel_coords_at_radius(target_voxel_coords: Tuple[int, int, int], radius: int, max_dims: Tuple[int, int, int]):
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
    # and replaces them with the corresponding coord of the boundary (origin or max_dims) 
    origin = np.array([0, 0, 0])
    # TODO: if possible - optimize later on (is it possible without looping?)
    # e.g. https://stackoverflow.com/questions/42150110/comparing-subarrays-in-numpy
    for v in voxels_at_radius:
        if (v < origin).any():
            voxels_at_radius = np.fmax(voxels_at_radius, origin)
        if (v > max_dims).any():
            voxels_at_radius = np.fmin(voxels_at_radius, max_dims)

    return voxels_at_radius

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

# target_voxel_coords = (5, 5)
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