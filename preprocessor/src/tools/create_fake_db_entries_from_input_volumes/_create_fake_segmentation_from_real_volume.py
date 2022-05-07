from pathlib import Path
from typing import Tuple, Dict
import numpy as np
from preprocessor.src.preprocessors.implementations.sff.preprocessor.sff_preprocessor import SFFPreprocessor
from preprocessor._old.check_internal_zarr import plot_3d_array_color

# small grid for now
# TODO: change to the biggest at EMDB
MAP_FILEPATH = Path('preprocessor\sample_volumes\emdb_sff\EMD-1832.map')

def create_fake_segmentation_from_real_volume(volume_filepath: Path, number_of_segments: int) -> Dict:
    prep = SFFPreprocessor()
    volume_grid: np.ndarray = prep.read_and_normalize_volume_map(volume_filepath)
    # empty segm grid
    segmentation_grid: np.ndarray = np.full(list(volume_grid.shape), fill_value=0, dtype=np.int32)
    assert segmentation_grid.dtype == np.int32
    assert segmentation_grid.shape == volume_grid.shape

    std = np.std(volume_grid)
    # be careful - there may be no point greater than certain sigma level (2, 1 etc.)
    isovalue_mask = volume_grid > 1 * std

    segm_ids = []
    for i in range(1, number_of_segments + 1):
        segm_ids.append(i)
        # coords of random 'True' from isovalue mask
        random_voxel_coords = get_coords_of_random_true_element(isovalue_mask)
        random_radius = get_random_radius(
            int(np.min(volume_grid.shape)/20),
            int(np.min(volume_grid.shape)/3)
            )
        
        shape_mask = get_shape_mask(random_voxel_coords, random_radius, segmentation_grid)
        
        # check if shape within isoval mask has some True in it
        # it should, otherwise segment id will be in list, but no such value will be on grid 
        shape_within_isoval_mask = shape_mask & isovalue_mask

        assert shape_within_isoval_mask.any()
        # print(f'Segm id: {i}, voxel values to be assigned: {segmentation_grid[shape_within_isoval_mask]}')
        segm_id = i
        segmentation_grid[shape_within_isoval_mask] = segm_id

        # update isovalue mask by removing shape we just assigned segm id to, from it
        isovalue_mask = logical_subtract(isovalue_mask, shape_within_isoval_mask)
        if isovalue_mask.any() == False:
            print(f'Last segment id is: {segm_id}. No space left for other segments')

    last_segm_id = number_of_segments + 1
    # TODO: uncomment or leave it like this
    # Fill remaining part of (all True left in isovalue mask) with one last segm id
    # segm_ids.append(last_segm_id)
    # segmentation_grid[isovalue_mask] = last_segm_id

    # checks if all segm ids are present in grid
    assert np.isin(np.array(segm_ids), segmentation_grid).all()

    grid_and_segm_ids = {
        'grid': segmentation_grid,
        'ids': segm_ids
    }
    return grid_and_segm_ids

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





