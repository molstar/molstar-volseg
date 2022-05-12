from pathlib import Path
from timeit import default_timer as timer
from itertools import combinations
import numpy as np
from typing import Dict
from preprocessor.src.preprocessors.implementations.sff.preprocessor.downsampling.downsampling import \
    generate_kernel_3d_arr

from preprocessor._old.check_internal_zarr import plot_volume_data_from_np_arr
from scipy import ndimage, signal
from preprocessor.src.preprocessors.implementations.sff.preprocessor.sff_preprocessor import SFFPreprocessor
from skimage.measure import block_reduce
from pprint import pprint

# TODO: put that on sabre
from preprocessor.src.tools.magic_kernel_downsampling_3d.magic_kernel_downsampling_3d import MagicKernel3dDownsampler

DATA_PATH = Path("../data/raw_input_files")
EMDB_DATA_PATH = DATA_PATH.joinpath("emdb")
# DUMMY_ARR_SHAPE = (500, 500, 500)
# DUMMY_ARR_SHAPE = (20,20,20)
# hardcoded for sabre
# 2000 * 2000 * 800 grid 
# REAL_MAP_FILEPATH = Path('emd_9199_.map')
# 64**3 grid
REAL_MAP_FILEPATH = EMDB_DATA_PATH.joinpath('emd-1832/emd-1832.map')
# 640**3 grid
# REAL_MAP_FILEPATH = Path('emd_13793.map')

ONE_D_KERNEL = [1, 4, 6, 4, 1]
LIST_OF_METHODS = [
    # 'for_loop',
    'scipy.ndimage.convolve_constant',
    'scipy.ndimage.convolve_reflect',
    'scipy.ndimage.convolve_mirror',
    'scipy.signal.convolve_fft',
    'scipy.signal.convolve_direct',
]

LIST_OF_MODES = [
    'regular',
    'average_2x2x2_blocks'
]


# TODO: typing unclear
def downsample_using_magic_kernel_wrapper(magic_kernel: MagicKernel3dDownsampler, method, mode, kernel, input_arr):
    '''
    Internally calls different implementations of convolve or previous magic kernel downsampling
    using for loop
    '''
    k = kernel
    a = input_arr
    r = np.array([0])
    # for now just method, add mode (avg over 2x2x2 blocks or simple) afterwards
    if method == 'for_loop':
        # it takes 1d kernel as tuple
        r = magic_kernel.downsample_using_magic_kernel(a, tuple(ONE_D_KERNEL))
    elif method == 'scipy.ndimage.convolve_constant':
        r = ndimage.convolve(a, k, mode='constant', cval=0.0)
    elif method == 'scipy.ndimage.convolve_reflect':
        r = ndimage.convolve(a, k, mode='reflect', cval=0.0)
    elif method == 'scipy.ndimage.convolve_mirror':
        r = ndimage.convolve(a, k, mode='mirror', cval=0.0)
    elif method == 'scipy.signal.convolve_direct':
        r = signal.convolve(a, k, mode='same', method='direct')
    elif method == 'scipy.signal.convolve_fft':
        r = signal.convolve(a, k, mode='same', method='fft')

    if mode == 'regular' and method != 'for_loop':
        r = r[::2, ::2, ::2]
    elif mode == 'average_2x2x2_blocks' and method != 'for_loop':
        rate = 2
        r = block_reduce(r, block_size=(rate, rate, rate), func=np.mean)
    # print(f'{method}, {mode}: downsampled data shape: {r.shape}')
    # print(r)
    return r


def read_real_volume_data(volume_file_path: Path) -> np.ndarray:
    # from some big map e.g. emd_9199_.map (2000*2000*800)
    prep = SFFPreprocessor()
    map_object = prep.read_volume_map_to_object(volume_file_path)
    normalized_axis_map_object = prep.normalize_axis_order(map_object)
    real_arr = prep.read_volume_data(normalized_axis_map_object)




    return real_arr


def run_benchmarking() -> Dict:
    '''
    Returns dict with benchmarking results
    '''
    magic_kernel = MagicKernel3dDownsampler()

    dict_of_results_by_approach: Dict = {}
    d = dict_of_results_by_approach

    kernel = generate_kernel_3d_arr(ONE_D_KERNEL)

    # dummy_arr = generate_dummy_arr(DUMMY_ARR_SHAPE).astype(np.float64)
    real_arr = read_real_volume_data(REAL_MAP_FILEPATH)
    dummy_arr = real_arr
    print(f'shape of volume is {dummy_arr.shape}')
    # print(f'ORIGINAL DATA')
    # print((dummy_arr))
    plot_volume_data_from_np_arr(dummy_arr, f'original_{dummy_arr.shape}-grid')
    for method in LIST_OF_METHODS:
        d[method] = {}
        for mode in LIST_OF_MODES:
            # there is just the downsampled voxels in for_loop method, nothing to average
            if method == 'for_loop' and mode == 'average_2x2x2_blocks':
                continue
            d[method][mode] = {}
            start = timer()
            d[method][mode] = downsample_using_magic_kernel_wrapper(magic_kernel, method, mode, kernel, dummy_arr)
            end = timer()
            print(f'{method}, {mode} took {end - start}')

    return d


def run_benchmarking_without_dict_plotting_one_by_one():
    magic_kernel = MagicKernel3dDownsampler()

    kernel = generate_kernel_3d_arr(ONE_D_KERNEL)

    # dummy_arr = generate_dummy_arr(DUMMY_ARR_SHAPE).astype(np.float64)
    real_arr = read_real_volume_data(REAL_MAP_FILEPATH)
    dummy_arr = real_arr
    print(f'shape of volume is {dummy_arr.shape}')
    # print(f'ORIGINAL DATA')
    # print((dummy_arr))
    plot_volume_data_from_np_arr(dummy_arr, f'original_{dummy_arr.shape}-grid')
    for method in LIST_OF_METHODS:
        for mode in LIST_OF_MODES:
            # there is just the downsampled voxels in for_loop method, nothing to average
            if method == 'for_loop' and mode == 'average_2x2x2_blocks':
                continue
            start = timer()
            downsampled_arr = downsample_using_magic_kernel_wrapper(magic_kernel, method, mode, kernel, dummy_arr)
            end = timer()
            print(f'{method}, {mode} took {end - start}')
            plot_volume_data_from_np_arr(downsampled_arr, f'{mode}_{method}_{downsampled_arr.shape}-grid')


def plot_everything(dict_with_arrs):
    # print('Plotting the following dict with arrs:')
    # print(dict_with_arrs)
    d = dict_with_arrs
    for method in d:
        for mode in d[method]:
            arr = d[method][mode]
            arr_name = f'{mode}_{method}_{arr.shape}-grid'
            plot_volume_data_from_np_arr(arr, arr_name)


def approximate_equality_check(dict_with_arrs):
    '''
    Warning. The results won't be equal as methods use different padding
    '''
    d = dict_with_arrs
    # dict where keys are modes
    per_mode_d = {}
    for mode in LIST_OF_MODES:
        per_mode_d[mode] = {}
        for method in d:
            if method == 'for_loop' and mode == 'average_2x2x2_blocks':
                continue
            if method == 'scipy.ndimage.convolve_reflect' or method == 'scipy.ndimage.convolve_mirror':
                continue
            arr = d[method][mode]
            per_mode_d[mode][f'{method}-{mode}'] = arr

    # print(f'per mode dict keys: {per_mode_d.keys()}')

    pairwise_approach_dict = {}

    for mode in LIST_OF_MODES:
        pairwise_approach_dict[mode] = {}
        for pair in combinations(per_mode_d[mode], 2):
            equal = np.all(np.isclose(per_mode_d[mode][pair[0]], per_mode_d[mode][pair[1]],
                                      rtol=1e-10,
                                      atol=1e-10,
                                      equal_nan=False))

            # dict with results of pairwise comparison of outcomes of each method
            pairwise_approach_dict[mode][f'{pair[0]}-vs-{pair[1]}'] = equal

    pprint(pairwise_approach_dict)


def run_regular_benchmarking():
    '''Results are collected into dict (requires more memory)'''
    d = run_benchmarking()
    plot_everything(d)


def run_one_by_one_benchmarking():
    '''Results are collected into dict (requires more memory). No equality check'''
    run_benchmarking_without_dict_plotting_one_by_one()


if __name__ == '__main__':
    # run_regular_benchmarking()
    run_one_by_one_benchmarking()
