import math

from cellstar_preprocessor.flows.zarr_methods import open_zarr
import dask.array as da
import zarr
from cellstar_preprocessor.flows.common import (
    compute_downsamplings_to_be_stored,
    compute_number_of_downsampling_steps,
)
from cellstar_preprocessor.flows.constants import (
    DOWNSAMPLING_KERNEL,
    MIN_GRID_SIZE,
    QUANTIZATION_DATA_DICT_ATTR_NAME,
    VOLUME_DATA_GROUPNAME,
)
from cellstar_preprocessor.flows.volume.helper_methods import (
    generate_kernel_3d_arr,
    store_volume_data_in_zarr_stucture,
)
from cellstar_preprocessor.model.volume import InternalVolume
from cellstar_preprocessor.tools.quantize_data.quantize_data import (
    decode_quantized_data,
)
from dask_image.ndfilters import convolve as dask_convolve


# this should work for e.g. ometiff
# potentially for several channels and timeframes
# could work via iterating over channels and timeframes in zarr structure
def volume_downsampling(internal_volume: InternalVolume):
    """
    Do downsamplings, store them in intermediate zarr structure
    Note: takes original data from 0th resolution, time_frame and channel
    """
    zarr_structure = open_zarr(
        internal_volume.path
    )
    # TODO: figure out how what to do in case of several channels (or time frames)
    # single resolution group "1"
    # N time groups
    # M channel groups
    # nested loops

    original_res_gr: zarr.Group = zarr_structure[VOLUME_DATA_GROUPNAME]["1"]
    for time, timegr in original_res_gr.groups():
        timegr: zarr.Group
        for channel_id, channel_arr in timegr.arrays():
            # NOTE: skipping convolve if one of dimensions is 1
            if 1 in channel_arr.shape:
                print(
                    f"Downsampling skipped for volume channel {channel_id}, timeframe {time}"
                )
                continue

            original_data_arr = zarr_structure[VOLUME_DATA_GROUPNAME]["1"][str(time)][
                str(channel_id)
            ]
            if QUANTIZATION_DATA_DICT_ATTR_NAME in original_data_arr.attrs:
                data_dict = original_data_arr.attrs[QUANTIZATION_DATA_DICT_ATTR_NAME]
                data_dict["data"] = da.from_zarr(url=original_data_arr)
                dask_arr: da.Array = decode_quantized_data(data_dict)
            else:
                dask_arr = da.from_zarr(
                    url=original_data_arr, chunks=original_data_arr.chunks
                )

            kernel = generate_kernel_3d_arr(list(DOWNSAMPLING_KERNEL))
            current_level_data = dask_arr

            # 1. compute number of downsampling steps based on internal_volume.downsampling
            # 2. compute list of ratios of downsamplings to be stored based on internal_volume.downsampling
            # 3. if ratio is in list, store it

            # downsampling_steps = 8
            downsampling_steps = compute_number_of_downsampling_steps(
                int_vol_or_seg=internal_volume,
                min_grid_size=MIN_GRID_SIZE,
                input_grid_size=math.prod(dask_arr.shape),
                factor=2**3,
                force_dtype=dask_arr.dtype,
            )

            ratios_to_be_stored = compute_downsamplings_to_be_stored(
                int_vol_or_seg=internal_volume,
                number_of_downsampling_steps=downsampling_steps,
                input_grid_size=math.prod(dask_arr.shape),
                factor=2**3,
                dtype=dask_arr.dtype,
            )
            for i in range(downsampling_steps):
                current_ratio = 2 ** (i + 1)
                downsampled_data = dask_convolve(
                    current_level_data, kernel, mode="mirror", cval=0.0
                )
                downsampled_data = downsampled_data[::2, ::2, ::2]

                if current_ratio in ratios_to_be_stored:
                    store_volume_data_in_zarr_stucture(
                        data=downsampled_data,
                        volume_data_group=zarr_structure[VOLUME_DATA_GROUPNAME],
                        params_for_storing=internal_volume.params_for_storing,
                        force_dtype=internal_volume.volume_force_dtype,
                        resolution=current_ratio,
                        time_frame=time,
                        channel=channel_id,
                    )

                current_level_data = downsampled_data
            print("Volume downsampled")

    # # NOTE: remove original level resolution data
    # if internal_volume.downsampling_parameters.remove_original_resolution:
    #     del zarr_structure[VOLUME_DATA_GROUPNAME]["1"]
    #     print("Original resolution data removed")
