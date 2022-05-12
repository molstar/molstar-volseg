from itertools import product
from typing import Tuple
import numpy as np
from math import ceil

class MagicKernel3dDownsampler():
    '''Deprecated. Own inefficient implementation of magic kernel downsampling. Current pipeline uses scipy convovle'''

    from ._helper_methods import compute_offset_indices_from_radius, setdiff2d_set, generate_dummy_arr

    def downsample_using_magic_kernel(self, arr: np.ndarray, kernel: Tuple[int, int, int, int, int]) -> np.ndarray:
        '''
        Returns x2 downsampled data using provided kernel
        '''
        # empty 3D arr with /2 dimensions compared to original 3D arr
        downsampled_arr = self.create_x2_downsampled_grid(arr.shape, np.nan)
        target_voxels_coords = self.extract_target_voxels_coords(arr.shape)

        #TODO: optimize using https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.convolve.html instead of for loop (for 1000**3 it consumes 12GB RAM)
        # Or use generator (expression or generator function
        # https://www.lachlaneagling.com/reducing-memory-consumption-python/
        # https://stackoverflow.com/questions/37156574/why-does-a-generator-expression-need-a-lot-of-memory

        for voxel_coords in target_voxels_coords:
            inner_layer_voxel_coords = self.get_voxel_coords_at_radius(voxel_coords, 1, arr.shape)
            outer_layer_voxel_coords = self.get_voxel_coords_at_radius(voxel_coords, 2, arr.shape)
            downsampled_voxel_value = self.compute_downsampled_voxel_value(
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

    def create_x2_downsampled_grid(self, original_grid_shape: tuple[int, int, int], fill_value) -> np.ndarray:
        empty_downsampled_grid = np.full([
            ceil(original_grid_shape[0] / 2),
            ceil(original_grid_shape[1] / 2),
            ceil(original_grid_shape[2] / 2)
        ], fill_value)
        return empty_downsampled_grid

    def extract_target_voxels_coords(self, arr_shape: tuple[int, int, int]):
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

    def get_voxel_coords_at_radius(self, target_voxel_coords: Tuple[int, int, int], radius: int, arr_shape: tuple[int, int, int]) -> list[int, int ,int]:
        '''
        Takes coords of a single target voxel and radius (e.g. 1 for inner, 2 for outer layer)
        and returns a list/arr of coords of voxels in surrounding depth layer according to radius
        '''
        # adapted with changes from: https://stackoverflow.com/a/34908879
        p = np.array(target_voxel_coords)
        ndim = len(p)
        # indices range for offsets for all layers (e.g. [-2, -1, 0, 1, 2])
        offset_idx_range_all_layers = self.compute_offset_indices_from_radius(radius)
        # indices range for offsets for just inner layers (e.g. [-1, 0, 1])
        offset_idx_range_inner_layers = self.compute_offset_indices_from_radius(radius - 1)

        # arr of all possible offsets if we select all layers (not just surface)
        offsets_all_layers = np.array(tuple(product(offset_idx_range_all_layers, repeat=ndim)))
        # arr of all possible offsets if we select just inner layers (except surface)
        offsets_inner_layers = np.array(tuple(product(offset_idx_range_inner_layers, repeat=ndim)))
        # arr of offsets corresponding to just surface layer (what is actually required)
        offsets_surface_layer = self.setdiff2d_set(offsets_all_layers, offsets_inner_layers)

        # TODO: assert if length of offsets_surface is equal to len offsets minus len offsets_inside

        # coords of voxels at given radius
        voxels_at_radius = p + offsets_surface_layer

        # Checks if (some, e.g. just x=-2) coords of some voxels are out of boundaries
        # and replaces them with the corresponding coord of the boundary (origin or max_grid_coords)
        origin = np.array([0, 0, 0])
        max_grid_coords = np.subtract(arr_shape, (1, 1, 1))
        # checking for possible out-of-bound indeces
        if (voxels_at_radius < origin).any():
            voxels_at_radius = np.fmax(voxels_at_radius, origin)

        # TODO: Type check
        if (voxels_at_radius > max_grid_coords).any():
            voxels_at_radius = np.fmin(voxels_at_radius, max_grid_coords)

        # in order to use it for indexing 3D array it needs to be a list of tuples, not np array
        voxels_at_radius = list(map(tuple, voxels_at_radius))
        return voxels_at_radius

    def compute_downsampled_voxel_value(self, arr: np.ndarray,
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
        coefficients_sum_3d = k[2] * 1 + k[1] * inner_layer_voxel_values.size + k[0] * outer_layer_voxel_values.size
        # print(f'coefficients sum is: {coefficients_sum_3d}')
        new_value = 1/coefficients_sum_3d * values_sum
        # print(values_sum)
        # print(new_value)
        return new_value
    
