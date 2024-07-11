import dask.array as da
import numpy as np
import zarr
from cellstar_preprocessor.flows.constants import (
    NON_QUANTIZED_DATA_TYPES_STR,
    QUANTIZATION_DATA_DICT_ATTR_NAME,
    VOLUME_DATA_GROUPNAME,
    VOLUME_DATA_GROUPNAME_COPY,
)
from cellstar_preprocessor.flows.zarr_methods import create_dataset_wrapper, open_zarr
from cellstar_preprocessor.model.volume import InternalVolume
from cellstar_preprocessor.tools.quantize_data.quantize_data import quantize_data


def _check_if_level_should_be_quantized(
    resolution: int, internal_volume: InternalVolume
):
    if internal_volume.quantize_downsampling_levels:
        if resolution in internal_volume.quantize_downsampling_levels:
            return True
        else:
            return False

    else:
        return True


def quantize_internal_volume(internal_volume: InternalVolume):
    if internal_volume.quantize_dtype_str and (
        (internal_volume.volume_force_dtype in (np.uint8, np.int8))
        or (
            (internal_volume.volume_force_dtype in (np.uint16, np.int16))
            and (
                internal_volume.quantize_dtype_str.value in NON_QUANTIZED_DATA_TYPES_STR
            )
        )
    ):
        print(
            f"Quantization is skipped because input volume dtype is {internal_volume.volume_force_dtype} and requested quantization dtype is {internal_volume.quantize_dtype_str.value}"
        )
        internal_volume.quantize_dtype_str = None

    if not internal_volume.quantize_dtype_str:
        raise Exception("No quantize dtype is provided")
    else:
        quantize_dtype_str = internal_volume.quantize_dtype_str

    zarr_structure: zarr.Group = open_zarr(internal_volume.path)

    # iterate over all arrays
    # create dask array

    # copy original volume data group
    zarr.copy_store(
        source=zarr_structure.store,
        dest=zarr_structure.store,
        source_path=VOLUME_DATA_GROUPNAME,
        dest_path=VOLUME_DATA_GROUPNAME_COPY,
    )

    # iterate over copy, delete original array (float dtype), recreate it with quantization dtype
    for res, res_gr in zarr_structure[VOLUME_DATA_GROUPNAME_COPY].groups():
        # if int(res) in internal_volume.quantize_downsampling_levels:
        if _check_if_level_should_be_quantized(
            resolution=int(res), internal_volume=internal_volume
        ):
            print(f"Downsampling level {res} will be quantized")
            for time, time_gr in res_gr.groups():
                for channel_arr_name, channel_arr in time_gr.arrays():
                    del zarr_structure[VOLUME_DATA_GROUPNAME][res][time][
                        channel_arr_name
                    ]

                    data = da.from_array(channel_arr)

                    quantized_data_dict = quantize_data(
                        data=data, output_dtype=quantize_dtype_str.value
                    )

                    data = quantized_data_dict["data"]

                    quantized_data_dict_without_data = quantized_data_dict.copy()
                    quantized_data_dict_without_data.pop("data")

                    zarr_arr = create_dataset_wrapper(
                        zarr_group=zarr_structure[VOLUME_DATA_GROUPNAME][res][time],
                        data=None,
                        name=str(channel_arr_name),
                        shape=data.shape,
                        dtype=data.dtype,
                        params_for_storing=internal_volume.params_for_storing,
                        is_empty=True,
                    )
                    # save this dict as attr of zarr arr
                    zarr_arr.attrs[QUANTIZATION_DATA_DICT_ATTR_NAME] = (
                        quantized_data_dict_without_data
                    )

                    # TODO: fix arr dtype
                    da.to_zarr(arr=data, url=zarr_arr, overwrite=True, compute=True)

    # remove copy
    del zarr_structure[VOLUME_DATA_GROUPNAME_COPY]

    print("Volume quantized")
