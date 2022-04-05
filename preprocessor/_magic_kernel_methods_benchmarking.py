
from timeit import default_timer as timer
from preprocessor._slicing_benchmarking import generate_dummy_arr
from typing import Dict
from preprocessor.check_internal_zarr import plot_volume_data_from_np_arr
from preprocessor._convolve_magic_kernel_experimental import generate_kernel_3d_arr
from scipy import ndimage, signal

DUMMY_ARR_SHAPE = (1000, 1000, 1000)
ONE_D_KERNEL = [1, 4, 6, 4, 1]

def downsample_using_magic_kernel_wrapper(method, mode, kernel, input_arr, OTHER_ARGS_TODO):
    '''
    Internally calls different implementations of convolve or previous magic kernel downsampling
    using for loop
    '''
    k = kernel
    a = input_arr

    # c_ndimage = ndimage.convolve(a, k, mode='constant', cval=0.0)
    # c_convolve = signal.convolve(a, k, mode='same', method='fft')
    # print(a)
    # print(c_ndimage[::2, ::2])
    # print(c_convolve[::2, ::2])

    # for now just method, add mode (avg over 2x2x2 blocks or simple) afterwards
    if method == _:
        pass
    elif method == _:
        pass
    # ..

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
            d[method][mode] = downsample_using_magic_kernel_wrapper(method, mode, kernel, dummy_arr, OTHER_ARGS_TODO)
            end = timer()
            print(f'{end - start}')

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