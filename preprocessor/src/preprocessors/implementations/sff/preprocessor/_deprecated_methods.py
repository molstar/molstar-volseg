import numpy as np


def downsample_categorical_data(self, arr: np.ndarray, rate: int) -> np.ndarray:
    '''Returns downsampled (every other value) np array. Deprecated'''
    if rate == 1:
        return arr
    # TODO: if choosing between '0' and non-zero value, it should perhaps leave non-zero value
    return arr[::rate, ::rate, ::rate]


def create_downsampling(original_data, rate, downsampled_data_group, isCategorical=False):
    '''Deprecated. Creates zarr array (dataset) filled with downsampled data'''
    # now this function is just for volume data dwnsmpling

    # not used as we switch to category-set-downsampling
    # if isCategorical:
    #     downsampled_data = __downsample_categorical_data(original_data, rate)
    # else:
    #     downsampled_data = __downsample_numerical_data(original_data, rate)

    downsampled_data = __downsample_numerical_data(original_data, rate)

    zarr_arr = downsampled_data_group.create_dataset(
        str(rate),
        shape=downsampled_data.shape,
        dtype=downsampled_data.dtype,
        # TODO: figure out how to determine optimal chunk size depending on the data
        chunks=(50, 50, 50)
    )
    zarr_arr[...] = downsampled_data


def __downsample_numerical_data(arr: np.ndarray, rate: int) -> np.ndarray:
    '''Deprecated. Returns downsampled (mean) np array'''
    if rate == 1:
        return arr
    # return block_reduce(arr, block_size=(rate, rate, rate), func=np.mean)
    # return downsample_using_magic_kernel(arr, DOWNSAMPLING_KERNEL)
