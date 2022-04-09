from pathlib import Path
from typing import Tuple
import numpy as np
from preprocessor.implementations.sff_preprocessor import SFFPreprocessor

# toy for now
# TODO:
MAP_FILEPATH = Path('preprocessor\sample_volumes\emdb_sff\EMD-1832.map')

def create_fake_segmentation_from_real_volume(volume_filepath: Path) -> np.ndarray:
    prep = SFFPreprocessor()
    volume_grid: np.ndarray = prep.read_and_normalize_volume_map(volume_filepath)
    # empty segm grid
    segmentation_grid: np.ndarray = np.full(list(volume_grid.shape), fill_value=0, dtype=np.int32)
    assert segmentation_grid.dtype == np.int32
    assert segmentation_grid.shape == volume_grid.shape

    std = np.std(volume_grid)
    isovalue_mask = volume_grid > 2 * std

    for i in range(1, 11):
        # coords of random 'True' from isovalue mask
        random_voxel_coords = get_coords_of_random_true_element(isovalue_mask)
        random_radius = get_random_radius(threshold = np.min(volume_grid.shape)/3)

        shape_mask = get_shape_mask(random_voxel_coords, random_radius)
        
        shape_within_isoval_mask = shape_mask & isovalue_mask

        # TODO: how to get segm id? 
        segm_id = i
        segmentation_grid[shape_within_isoval_mask] = segm_id

        # update isovalue mask by removing shape we just assigned segm id to, from it
        isovalue_mask = logical_subtract(isovalue_mask, shape_within_isoval_mask)

    # TODO: how to get last segm_id?
    last_segm_id = 100
    # Fill remaining part of (all True left in isovalue mask) with one last segm id
    segmentation_grid[isovalue_mask] = last_segm_id



def get_shape_mask(center_coords: Tuple[int, int, int], radius: int, arr: np.ndarray):
    cx, cy, cz = center_coords
    sx, sy, sz = arr.shape
    x, y, z = np.ogrid[:sx, :sy, :sz]
    mask = (x - cx)**2 + (y - cy)**2 + (z - cz)**2 <= radius**2
    return mask

def logical_subtract(A, B):
    '''For subtracting boolean arrays (kinda set difference)'''
    # Source: https://github.com/numpy/numpy/issues/15856
    return A.astype(np.int) - B.astype(np.int) == 1

def get_coords_of_random_true_element(mask: np.ndarray) -> Tuple[int, int, int]:
    '''Get coordinates (indices) of random voxel in mask that is equal to True'''
    # TODO:
    pass

def get_random_radius(threshold: int) -> int:
    # TODO: google how to generate random number withing range
    return 10


if __name__ == '__main__':
    create_fake_segmentation_from_real_volume(MAP_FILEPATH)






