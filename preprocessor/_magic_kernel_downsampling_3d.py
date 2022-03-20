from itertools import product
from typing import Tuple
import numpy as np

def extract_target_voxel_coords():
    '''
    Takes 3d arr and extract target voxel coordinates (every other in all three dimensions)
    '''
    # repeat - n of dimensions, list = list of values of group for that permutation
    # TODO: determine lst based on grid dimensions
    lst = [0, 2, 4]
    permutations = product(lst, repeat=3)
    # TODO: assert permutations == grid x/2 y/2 z/2
    return tuple(permutations)

def get_surrounding_voxels_coords(target_voxel_coords: Tuple[int, int, int], radius: int):
    '''
    Takes target voxel coordinates and radius (e.g. 1 for inner, 2 for outer layer)
    and returns a list/arr of coords for surrounding depth according to radius
    '''
    # adapted with changes from: https://stackoverflow.com/a/34908879
    # TODO: shape=None overflow - do we need it?
    p = np.array(target_voxel_coords)
    ndim = len(p)
    # TODO: determine lst based on provided radius
    # TODO: !IMPORTANT figure out how to produce outer layer. -2 -1 0 1 2 may not work!
    lst = [-1, 0, 1]
    offsets = np.array(tuple(product(lst, repeat=3)))
    # excludes 0, 0, 0 offset (target voxel itself)
    offsets = offsets[np.any(offsets, 1)]
    # TODO: assert if length of offsets is minus one (if point itself is removed)
    # TODO: figure out how to do this check for outer layer
    neighbours = p + offsets
    return neighbours


