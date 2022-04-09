from pathlib import Path
from typing import Tuple
import numpy as np
from preprocessor.implementations.sff_preprocessor import SFFPreprocessor
from preprocessor.check_internal_zarr import plot_3d_array_color

# small grid for now
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
    # be careful - there may be no point greater than certain sigma level (2, 1 etc.)
    isovalue_mask = volume_grid > 1 * std

    for i in range(1, 11):
        # coords of random 'True' from isovalue mask
        random_voxel_coords = get_coords_of_random_true_element(isovalue_mask)
        random_radius = get_random_radius(
            int(np.min(volume_grid.shape)/20),
            int(np.min(volume_grid.shape)/3)
            )

        shape_mask = get_shape_mask(random_voxel_coords, random_radius, segmentation_grid)
        
        shape_within_isoval_mask = shape_mask# & isovalue_mask

        # TODO: how to get segm id? 
        segm_id = i
        segmentation_grid[shape_within_isoval_mask] = segm_id

        # update isovalue mask by removing shape we just assigned segm id to, from it
        isovalue_mask = logical_subtract(isovalue_mask, shape_within_isoval_mask)

    # TODO: how to get last segm_id?
    last_segm_id = 100
    # TODO: uncomment
    # Fill remaining part of (all True left in isovalue mask) with one last segm id
    # segmentation_grid[isovalue_mask] = last_segm_id
    return segmentation_grid


def get_shape_mask(center_coords: Tuple[int, int, int], radius: int, arr: np.ndarray):
    cx, cy, cz = center_coords
    sx, sy, sz = arr.shape
    x, y, z = np.ogrid[:sx, :sy, :sz]
    mask = (x - cx)**2 + (y - cy)**2 + (z - cz)**2 <= radius**2
    return mask

def logical_subtract(A, B):
    '''For subtracting boolean arrays (kinda set difference)'''
    # Source: https://github.com/numpy/numpy/issues/15856
    return A.astype(np.int32) - B.astype(np.int32) == 1

def get_coords_of_random_true_element(mask: np.ndarray) -> Tuple[int, int, int]:
    '''Get coordinates (indices) of random voxel in mask that is equal to True'''
    x,y,z = np.where(mask == True)
    i = np.random.randint(len(x))
    random_position = (x[i], y[i], z[i])
    return random_position
    

def get_random_radius(min_value: int, max_value: int) -> int:
    return np.random.randint(min_value, max_value)

if __name__ == '__main__':
    fake_segm = create_fake_segmentation_from_real_volume(MAP_FILEPATH)
    # with np.printoptions(threshold=np.inf):
    #     print(fake_segm[fake_segm.nonzero()])
    plot_3d_array_color(fake_segm, 'fake_segm')





