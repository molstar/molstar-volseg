
from timeit import default_timer as timer
from preprocessor._slicing_benchmarking import generate_dummy_arr
from typing import Dict
from preprocessor.check_internal_zarr import plot_volume_data_from_np_arr

DUMMY_ARR_SHAPE = (1000, 1000, 1000)

def run_benchmarking() -> Dict:
    '''
    Returns dict with benchmarking results
    '''
    dict_of_results_by_approach: Dict = {}
    d = dict_of_results_by_approach

    dummy_arr = generate_dummy_arr(DUMMY_ARR_SHAPE)
    for method in LIST_OF_METHODS:
        d[method] = {}
        for mode in LIST_OF_MODES:
            d[method][mode] = {}
            start = timer()
            d[method][mode] = downsample_using_magic_kernel_wrapper(method, mode, OTHER_ARGS_TODO)
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