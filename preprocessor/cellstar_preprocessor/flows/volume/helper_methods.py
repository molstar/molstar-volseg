import logging
import math

import dask.array as da
import numpy as np
import zarr
from cellstar_preprocessor.flows.common import create_dataset_wrapper


def generate_kernel_3d_arr(pattern: list[int]) -> np.ndarray:
    """
    Generates conv kernel based on pattern provided (e.g. [1,4,6,4,1]).
    https://stackoverflow.com/questions/71739757/generate-3d-numpy-array-based-on-provided-pattern/71742892#71742892
    """
    try:
        assert len(pattern) == 5, "pattern should have length 5"
        pattern = pattern[0:3]
        x = np.array(pattern[-1]).reshape([1, 1, 1])
        for p in reversed(pattern[:-1]):
            x = np.pad(x, mode="constant", constant_values=p, pad_width=1)

        k = (1 / x.sum()) * x
        assert k.shape == (5, 5, 5)
    except AssertionError as e:
        logging.error(e, stack_info=True, exc_info=True)
        raise e
    return k


def __compute_number_of_downsampling_steps(
    *,
    min_grid_size: int,
    input_grid_size: int,
    force_dtype: np.dtype,
    factor: int,
    min_downsampled_file_size_bytes: int = 5 * 10**6,
) -> int:
    """
    Old version
    """
    # if there are min and max downsampling level in internal_volume.downsampling
    # return  max - min / 2

    if input_grid_size <= min_grid_size:
        return 1
    # num_of_downsampling_steps: int = math.ceil(math.log2(input_grid_size/min_grid_size))
    x1_filesize_bytes: int = input_grid_size * force_dtype.itemsize
    num_of_downsampling_steps: int = int(
        math.log(x1_filesize_bytes / min_downsampled_file_size_bytes, factor)
    )
    if num_of_downsampling_steps <= 1:
        return 1
    return num_of_downsampling_steps

    # should it output some kind of downsampling curve? e.g. [4, 8, 16, 32]


def normalize_axis_order_mrcfile(dask_arr: da.Array, mrc_header: object) -> da.Array:
    """
    Normalizes axis order to X, Y, Z (1, 2, 3)
    """
    h = mrc_header
    current_order = int(h.mapc) - 1, int(h.mapr) - 1, int(h.maps) - 1

    if current_order != (0, 1, 2):
        print(f"Reordering axes from {current_order}...")
        ao = {v: i for i, v in enumerate(current_order)}
        # TODO: optimize this to a single transpose
        dask_arr = dask_arr.transpose().transpose(ao[2], ao[1], ao[0]).transpose()
    else:
        dask_arr = dask_arr.transpose()

    return dask_arr


def store_volume_data_in_zarr_stucture(
    data: da.Array,
    volume_data_group: zarr.Group,
    params_for_storing: dict,
    force_dtype: np.dtype,
    resolution: str,
    time_frame: str,
    channel: str,
    # quantize_dtype_str: Union[QuantizationDtype, None] = None
):
    resolution_data_group: zarr.Group = volume_data_group.require_group(resolution)
    time_frame_data_group = resolution_data_group.require_group(time_frame)

    # if quantize_dtype_str:
    #     force_dtype = quantize_dtype_str.value

    zarr_arr = create_dataset_wrapper(
        zarr_group=time_frame_data_group,
        data=None,
        name=str(channel),
        shape=data.shape,
        dtype=force_dtype,
        params_for_storing=params_for_storing,
        is_empty=True,
    )

    # if quantize_dtype_str:
    #     quantized_data_dict = quantize_data(
    #         data=data,
    #         output_dtype=quantize_dtype_str.value)

    #     data = quantized_data_dict["data"]

    #     quantized_data_dict_without_data = quantized_data_dict.copy()
    #     quantized_data_dict_without_data.pop('data')

    #     # save this dict as attr of zarr arr
    #     zarr_arr.attrs[QUANTIZATION_DATA_DICT_ATTR_NAME] = quantized_data_dict_without_data

    da.to_zarr(arr=data, url=zarr_arr, overwrite=True, compute=True)
