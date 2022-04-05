
from timeit import default_timer as timer

import numpy as np
from preprocessor._slicing_benchmarking import generate_dummy_arr
from typing import Dict
from preprocessor.check_internal_zarr import plot_volume_data_from_np_arr
from preprocessor._convolve_magic_kernel_experimental import generate_kernel_3d_arr
from scipy import ndimage, signal
from preprocessor.implementations.sff_preprocessor import downsample_using_magic_kernel

# TODO: put that on sabre
# DUMMY_ARR_SHAPE = (1000, 1000, 1000)
DUMMY_ARR_SHAPE = (50, 50, 50)

ONE_D_KERNEL = [1, 4, 6, 4, 1]
LIST_OF_METHODS = [
    'for_loop',
    'scipy.ndimage.convolve',
    'scipy.signal.convolve_fft',
    'scipy.signal.convolve_direct',
]

LIST_OF_MODES = [
    'regular'
    # TODO: add mode for averaging over eight 2x2x2 blocks instead of ::2 ::2 ::2
]

def downsample_using_magic_kernel_wrapper(method, mode, kernel, input_arr):
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
        r = downsample_using_magic_kernel(a, tuple(ONE_D_KERNEL))
    elif method == 'scipy.ndimage.convolve':
        r = ndimage.convolve(a, k, mode='constant', cval=0.0)
    elif method == 'scipy.signal.convolve_direct':
        r = signal.convolve(a, k, mode='same', method='direct')
    elif method == 'scipy.signal.convolve_fft':
        r = signal.convolve(a, k, mode='same', method='fft')

    # TODO: add mode for averaging 2x2x2
    if mode == 'regular' and method != 'for_loop':
        r = r[::2, ::2, ::2]
    # ... other?
    return r

def run_benchmarking() -> Dict:
    '''
    Returns dict with benchmarking results
    '''
    dict_of_results_by_approach: Dict = {}
    d = dict_of_results_by_approach

    kernel = generate_kernel_3d_arr(ONE_D_KERNEL)

    dummy_arr = generate_dummy_arr(DUMMY_ARR_SHAPE)
    for method in LIST_OF_METHODS:
        d[method] = {}
        for mode in LIST_OF_MODES:
            d[method][mode] = {}
            start = timer()
            d[method][mode] = downsample_using_magic_kernel_wrapper(method, mode, kernel, dummy_arr)
            end = timer()
            print(f'{method}, {mode} took {end - start}')

    return d

def plot_everything(dict_with_arrs):
    d = dict_with_arrs
    for method in d:
        for mode in d[method]:
            arr = d[method][mode]
            arr_name = f'{mode}_{method}'
            plot_volume_data_from_np_arr(arr, arr_name)

if __name__ == '__main__':
    # __testing()
    d = run_benchmarking()
    plot_everything(d)