from pathlib import Path
from typing import Tuple, Dict
import numpy as np
from preprocessor.implementations.sff_preprocessor import SFFPreprocessor
from preprocessor.check_internal_zarr import plot_3d_array_color

# small grid for now
# TODO: change to the biggest at EMDB
MAP_FILEPATH = Path('preprocessor\sample_volumes\emdb_sff\EMD-1832.map')

def create_fake_segmentation_from_real_volume(volume_filepath: Path, number_of_segments: int) -> Dict:
    prep = SFFPreprocessor()
    map_and_rmsd = prep.read_and_normalize_volume_map_and_get_rmsd(volume_filepath)
    volume_grid: np.ndarray = map_and_rmsd['map']
    # not std but rmsd
    std = map_and_rmsd['rmsd']
    # empty segm grid
    # trying uint8 to reduce the memory consumption
    # todo: make it mmap ndarray? 
    segmentation_grid: np.ndarray = np.full(list(volume_grid.shape), fill_value=0, dtype=np.uint8)
    assert segmentation_grid.dtype == np.uint8
    assert segmentation_grid.shape == volume_grid.shape

    # we can use std that they have in map file, as calc this potentially creates memory issues
    # or we can calc std in other way
    # std = np.std(volume_grid)
    # be careful - there may be no point greater than certain sigma level (2, 1 etc.)
    print('isovalue mask creation started')
    isovalue_mask = volume_grid > 1 * std
    print('isovalue mask created')
    
    segm_ids = []
    print('segments creation started in for loop')
    for i in range(1, number_of_segments + 1):
        print(f'segment {i} creation started')
        segm_ids.append(i)
        # coords of random 'True' from isovalue mask
        random_voxel_coords = get_coords_of_random_true_element(isovalue_mask)
        print(f'random voxel coords generated {random_voxel_coords}')
        random_radius = get_random_radius(
            int(np.min(volume_grid.shape)/20),
            int(np.min(volume_grid.shape)/3)
            )

        print(f'random radius generated: {random_radius}')
        
        shape_mask = get_shape_mask(random_voxel_coords, random_radius, segmentation_grid)
        print(f'shape mask generated {shape_mask.shape}')
        # check if shape within isoval mask has some True in it
        # it should, otherwise segment id will be in list, but no such value will be on grid 
        shape_within_isoval_mask = shape_mask & isovalue_mask
        print('shape mask within isovalue generated')

        assert shape_within_isoval_mask.any()
        # print(f'Segm id: {i}, voxel values to be assigned: {segmentation_grid[shape_within_isoval_mask]}')
        segm_id = i
        segmentation_grid[shape_within_isoval_mask] = segm_id
        print('segment drawn in segmentation grid')

        # update isovalue mask by removing shape we just assigned segm id to, from it
        isovalue_mask = logical_subtract(isovalue_mask, shape_within_isoval_mask)
        print('isovalue mask updated (subtract recently created segment)')
        if isovalue_mask.any() == False:
            print(f'Last segment id is: {segm_id}. No space left for other segments')

    last_segm_id = number_of_segments + 1
    # TODO: uncomment or leave it like this
    # Fill remaining part of (all True left in isovalue mask) with one last segm id
    # segm_ids.append(last_segm_id)
    # segmentation_grid[isovalue_mask] = last_segm_id

    # checks if all segm ids are present in grid
    assert np.isin(np.array(segm_ids), segmentation_grid).all()
    print('check performed if all segm ids are present in grid')

    grid_and_segm_ids = {
        'grid': segmentation_grid,
        'ids': segm_ids
    }
    print('gird_and_segm_ids dict assigned, next is return')
    return grid_and_segm_ids

def get_shape_mask(center_coords: Tuple[int, int, int], radius: int, arr: np.ndarray):
    cx, cy, cz = center_coords
    sx, sy, sz = arr.shape
    print('ogrid is being created')
    x, y, z = np.ogrid[:sx, :sy, :sz]
    print('ogrid is created')
    mask = (x - cx)**2 + (y - cy)**2 + (z - cz)**2 <= radius**2
    print(f'mask is created, mask shape: {mask.shape}')
    return mask

def logical_subtract(A, B):
    '''For subtracting boolean arrays (kinda set difference)'''
    # Source: https://github.com/numpy/numpy/issues/15856
    return A.astype(np.int32) - B.astype(np.int32) == 1

def get_random_arr_position_based_on_condition(arr: np.ndarray, condition=True):
    '''Deprecated. Too deep recursion'''
    x, y, z = arr.shape
    rx = np.random.randint(x)
    ry = np.random.randint(y)
    rz = np.random.randint(z)
    # TODO: if recursion is too deep, google how to make linear iterative recursion
    # (precise term in scip book)
    # could be for loop or generator instead (call function until result is satisfactory)
    if (arr[rx, ry, rz] == condition):
        return (rx, ry, rz)
    else:
        return get_random_arr_position_based_on_condition(arr, condition)

def get_random_arr_position(arr):
    x, y, z = arr.shape
    rx = np.random.randint(x)
    ry = np.random.randint(y)
    rz = np.random.randint(z)
    return (rx, ry, rz)

def get_coords_of_random_true_element(mask: np.ndarray) -> Tuple[int, int, int]:
    '''Get coordinates (indices) of random voxel in mask that is equal to True'''
    # For 2000*2000*800 grid it results in 82GB RAM tuple (x,y,z)
    # x,y,z = np.where(mask == True)
    # i = np.random.randint(len(x))
    # random_position = (x[i], y[i], z[i])
    rx, ry, rz = get_random_arr_position(mask)
    while mask[rx, ry, rz] != True:
        rx, ry, rz = get_random_arr_position(mask)

    return (rx, ry, rz)
    

def get_random_radius(min_value: int, max_value: int) -> int:
    return np.random.randint(min_value, max_value)

if __name__ == '__main__':
    fake_segm = create_fake_segmentation_from_real_volume(MAP_FILEPATH, 10)
    # with np.printoptions(threshold=np.inf):
    #     print(fake_segm[fake_segm.nonzero()])
    plot_3d_array_color(fake_segm, 'fake_segm')





