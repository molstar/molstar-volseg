from pathlib import Path
from typing import Tuple, Dict
import numpy as np
from preprocessor.implementations.sff_preprocessor import SFFPreprocessor
from preprocessor.check_internal_zarr import plot_3d_array_color

# small grid for now
# TODO: change to the biggest at EMDB
MAP_FILEPATH = Path('preprocessor\sample_volumes\emdb_sff\EMD-1832.map')

def _if_position_satisfy_sphere_equation(
        r: int, center_coords: Tuple[int, int, int],
        position: Tuple[int, int, int]
        ) -> bool:
    cx, cy, cz = center_coords
    x, y, z = position
    if (x - cx)**2 + (y - cy)**2 + (z - cz)**2 <= r**2:
        return True
    return False

def create_fake_segmentation_from_real_volume(volume_filepath: Path, number_of_segments: int) -> Dict:
    prep = SFFPreprocessor()
    map_and_rmsd = prep.read_and_normalize_volume_map_and_get_rmsd(volume_filepath)
    volume_grid: np.ndarray = map_and_rmsd['map']
    # not std but rmsd
    std = map_and_rmsd['rmsd']
    isosurface_threshold = 1 * std
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
    
    segm_ids = []
    print('segments creation started in for loop')
    for i in range(1, number_of_segments + 1):
        print(f'segment {i} creation started')
        segm_ids.append(i)
        # coords of random voxel
        random_voxel_coords = get_coords_of_random_position_inside_isosurface(
            volume_grid,
            segmentation_grid,
            isosurface_threshold)
        print(f'random voxel coords generated {random_voxel_coords}')
        random_radius = get_random_radius(
            int(np.min(volume_grid.shape)/20),
            int(np.min(volume_grid.shape)/3)
            )
        print(f'random radius generated: {random_radius}')
        
        segm_id = i

        for index in np.ndindex(volume_grid.shape):
            # returns tuple of indices
            # TODO: multiple conditions (nested ifs) can be optimized?
            if volume_grid[index] > isosurface_threshold:
                # if not assigned to other segm id
                if segmentation_grid[index] == 0:
                    if _if_position_satisfy_sphere_equation(random_radius, random_voxel_coords, index) == True:
                        segmentation_grid[index] = segm_id
        print(f'segment {segm_id} written on segm grid')
        print(f'there are {segmentation_grid[segmentation_grid == segm_id].shape} instances of that segment on segm grid')
        # TODO: check if previous issuew with segment id will be in list,
        # but with no such value on grid can pop with iterative implementation
        
        # TODO: implement some warning in case there is no space left for the remaining segments
        # if first several segments occupied all space alread

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
    print('gird_and_segm_ids dict assigned, next is return statement')
    return grid_and_segm_ids

def get_shape_mask(center_coords: Tuple[int, int, int], radius: int, arr: np.ndarray):
    cx, cy, cz = center_coords
    sx, sy, sz = arr.shape
    print('ogrid is being created')
    x, y, z = np.ogrid[:sx, :sy, :sz]
    print('ogrid is created')
    # TODO: switch all three to numpy memmap?
    # TODO: delete vars after they are used?
    # (818, 1, 1) arr
    mask_x = (x - cx)**2
    # (1, 2134, 1) arr
    mask_y = (y - cy)**2
    mask_z = (z - cz)**2
    radius_squared = radius**2
    # CAREFUL: the following line eats all 32GB RAM
    # when executed second time in interpreter, process get killed. first time - ok
    # possibly because mask sum contains values like 897203? idk
    print('components of sphere equation are calculated')
    del x, y, z
    print('ogrid components deleted from RAM')
    mask_sum = mask_x + mask_y + mask_z
    print('mask sum is calculated')
    
    mask = mask_sum <= radius_squared
    print(f'mask is created, mask shape: {mask.shape}')
    del mask_sum
    print('mask_sum is deleted from RAM')
    return mask

def logical_subtract(A, B):
    '''For subtracting boolean arrays (kinda set difference)'''
    # Source: https://github.com/numpy/numpy/issues/15856
    return A.astype(np.int32) - B.astype(np.int32) == 1

def get_random_arr_position(arr):
    x, y, z = arr.shape
    rx = np.random.randint(x)
    ry = np.random.randint(y)
    rz = np.random.randint(z)
    return (rx, ry, rz)

def get_coords_of_random_position_inside_isosurface(
    volume_arr: np.ndarray,
    segm_arr: np.ndarray,
    threshold) -> Tuple[int, int, int]:
    '''Get coordinates (indices) of random voxel in grid that is inside isosurface'''
    rx, ry, rz = get_random_arr_position(volume_arr)
    while volume_arr[rx, ry, rz] <= threshold or segm_arr[rx, ry, rz] != 0:
        rx, ry, rz = get_random_arr_position(volume_arr)

    return (rx, ry, rz)
    

def get_random_radius(min_value: int, max_value: int) -> int:
    return np.random.randint(min_value, max_value)

if __name__ == '__main__':
    fake_segm = create_fake_segmentation_from_real_volume(MAP_FILEPATH, 10)
    # with np.printoptions(threshold=np.inf):
    #     print(fake_segm[fake_segm.nonzero()])
    plot_3d_array_color(fake_segm, 'fake_segm')





