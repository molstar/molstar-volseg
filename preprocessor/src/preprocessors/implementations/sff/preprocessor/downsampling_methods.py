import math
from typing import Dict, List
import zarr
import numpy as np
from preprocessor.src.preprocessors.implementations.sff.preprocessor.sff_preprocessor import DOWNSAMPLING_KERNEL, MIN_DOWNSAMPLING_VOLUME_FILESIZE
from volume_server.preprocessed_volume_to_cif.implementations.ciftools_converter.Categories import segmentation_table
from scipy import signal

def compute_number_of_downsampling_steps(min_grid_size: int, input_grid_size: int, force_dtype: type, factor: int) -> int:
    if input_grid_size <= min_grid_size:
        return 1
    # num_of_downsampling_steps: int = math.ceil(math.log2(input_grid_size/min_grid_size))
    x1_filesize_bytes: int = input_grid_size * force_dtype().itemsize
    downsampling_factor = factor
    # if x1_filesize_bytes / MIN_DOWNSAMPLING_VOLUME_FILESIZE < 1? TODO: fix
    # ratio: int = int(int(x1_filesize_bytes / MIN_DOWNSAMPLING_VOLUME_FILESIZE) / downsampling_factor)
    num_of_downsampling_steps: int = int(math.log(
        x1_filesize_bytes / MIN_DOWNSAMPLING_VOLUME_FILESIZE,
        factor
    ))
    if num_of_downsampling_steps <= 1:
        return 1
    return num_of_downsampling_steps

def create_volume_downsamplings(original_data: np.ndarray, downsampling_steps: int, downsampled_data_group: zarr.hierarchy.Group, force_dtype=np.float32):
    '''
    Take original volume data, do all downsampling levels and store in zarr struct one by one
    '''
    # TODO: do we need to make it uniform float64 as other other level grids? x1 is float32
    # original_data = original_data.astype(np.float)
    current_level_data = original_data
    self.__store_single_volume_downsampling_in_zarr_stucture(current_level_data, downsampled_data_group, 1)
    for i in range(downsampling_steps):
        current_ratio = 2**(i + 1)
        
        # switching to convolve
        # downsampled_data = downsample_using_magic_kernel(current_level_data, DOWNSAMPLING_KERNEL)
        kernel = self.generate_kernel_3d_arr(list(DOWNSAMPLING_KERNEL))
        downsampled_data = signal.convolve(current_level_data, kernel, mode='same', method='fft')
        downsampled_data = downsampled_data[::2, ::2, ::2]
        
        self.__store_single_volume_downsampling_in_zarr_stucture(downsampled_data, downsampled_data_group, current_ratio, force_dtype)
        current_level_data = downsampled_data
    # # TODO: figure out compression/filters: b64 encoded zlib-zipped .data is just 8 bytes
    # downsamplings sizes in raw uncompressed state are much bigger 
    # TODO: figure out what to do with chunks - currently their size is not optimized

def create_category_set_downsamplings(
    original_data: np.ndarray,
    downsampling_steps: int,
    downsampled_data_group: zarr.hierarchy.Group,
    value_to_segment_id_dict_for_specific_lattice_id: Dict
    ):
    '''
    Take original segmentation data, do all downsampling levels, create zarr datasets for each
    '''
    # table with just singletons, e.g. "104": {104}, "94" :{94}
    initial_set_table = segmentation_table(original_data, value_to_segment_id_dict_for_specific_lattice_id)
    
    # to make it uniform int32 with other level grids
    original_data = original_data.astype(np.int32)

    # for now contains just x1 downsampling lvl dict, in loop new dicts for new levels are appended
    levels = [
        DownsamplingLevelDict({'ratio': 1, 'grid': original_data, 'set_table': initial_set_table})
        ]
    for i in range(downsampling_steps):
        current_set_table = SegmentationSetTable(original_data, value_to_segment_id_dict_for_specific_lattice_id)
        # on first iteration (i.e. when doing x2 downsampling), it takes original_data and initial_set_table with set of singletons 
        levels.append(self.__downsample_categorical_data_using_category_sets(levels[i], current_set_table))

    # store levels list in zarr structure (can be separate function)
    self.__store_downsampling_levels_in_zarr_structure(levels, downsampled_data_group)

def __store_single_volume_downsampling_in_zarr_stucture(downsampled_data: np.ndarray, downsampled_data_group: zarr.hierarchy.Group, ratio: int, force_dtype=np.float32):
    downsampled_data_group.create_dataset(
        data=downsampled_data.astype(force_dtype),
        name=str(ratio),
        shape=downsampled_data.shape,
        # just change dtype for storing 
        dtype=force_dtype,
        # # TODO: figure out how to determine optimal chunk size depending on the data
        chunks=(50, 50, 50)
    )

def generate_kernel_3d_arr(pattern: List[int]) -> np.ndarray:
    '''
    Generates conv kernel based on pattern provided (e.g. [1,4,6,4,1]).
    https://stackoverflow.com/questions/71739757/generate-3d-numpy-array-based-on-provided-pattern/71742892#71742892
    '''
    pattern = pattern[0:3]
    x = np.array(pattern[-1]).reshape([1,1,1])
    for p in reversed(pattern[:-1]):
        x = np.pad(x, mode='constant', constant_values=p, pad_width=1)
    
    k = (1/x.sum()) * x
    # print(f'Kernel generated (further divided by sum): {x}')
    return k