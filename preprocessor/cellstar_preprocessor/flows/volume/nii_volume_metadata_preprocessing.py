from decimal import Decimal

from cellstar_preprocessor.flows.zarr_methods import open_zarr
import dask.array as da
import numpy as np
from cellstar_db.models import (
    DownsamplingLevelInfo,
    TimeInfo,
    VolumeSamplingInfo,
    VolumesMetadata,
)
from cellstar_preprocessor.flows.zarr_methods import (
    get_downsamplings,
)
from cellstar_preprocessor.flows.constants import (
    QUANTIZATION_DATA_DICT_ATTR_NAME,
    VOLUME_DATA_GROUPNAME,
)
from cellstar_preprocessor.model.volume import InternalVolume
from cellstar_preprocessor.tools.quantize_data.quantize_data import (
    decode_quantized_data,
)


def _get_source_axes_units(nii_header):
    # spatial_units = nii_header.get_xyzt_units()[0]
    # NOTE: hardcoding this
    spatial_units = "angstrom"
    d = {"x": spatial_units, "y": spatial_units, "z": spatial_units}
    return d


def _get_voxel_sizes_in_downsamplings(
    nii_header, volume_downsamplings: list[DownsamplingLevelInfo]
):
    # TODO: hardcoding this (mistake in header, correct size for mouse github dataset x = 16 nm, y = 16 nm, and z = 15 nm)
    # pixdim = nii_header['pixdim']
    # original_voxel_size = (pixdim[1], pixdim[2], pixdim[3])
    original_voxel_size = (160, 160, 150)

    voxel_sizes_in_downsamplings: dict = {}
    for level in volume_downsamplings:
        rate = level["level"]
        voxel_sizes_in_downsamplings[rate] = tuple(
            [float(Decimal(float(i)) * Decimal(rate)) for i in original_voxel_size]
        )
    return voxel_sizes_in_downsamplings


def _get_nii_volume_sampling_info(
    root_data_group,
    sampling_info_dict,
    nii_header: object,
    volume_downsamplings: list[DownsamplingLevelInfo],
):
    voxel_sizes_in_downsamplings = _get_voxel_sizes_in_downsamplings(
        nii_header=nii_header, volume_downsamplings=volume_downsamplings
    )
    # NOTE: not clear where to get origin from
    origin = (0, 0, 0)

    for res_gr_name, res_gr in root_data_group.groups():
        # create layers (time gr, channel gr)
        sampling_info_dict.boxes[res_gr_name] = {
            "origin": origin,
            "voxel_size": voxel_sizes_in_downsamplings[int(res_gr_name)],
            "grid_dimensions": None,
            # 'force_dtype': None
        }

        sampling_info_dict.descriptive_statistics[res_gr_name] = {}

        for time_gr_name, time_gr in res_gr.groups():
            first_group_key = sorted(time_gr.array_keys())[0]

            sampling_info_dict.boxes[res_gr_name].grid_dimensions = time_gr[
                first_group_key
            ].shape
            # sampling_info_dict['boxes'][res_gr_name]['force_dtype'] = time_gr[first_group_key].dtype.str

            sampling_info_dict.descriptive_statistics[res_gr_name][time_gr_name] = {}
            for channel_arr_name, channel_arr in time_gr.arrays():
                assert (
                    sampling_info_dict.boxes[res_gr_name].grid_dimensions
                    == channel_arr.shape
                )
                # assert sampling_info_dict['boxes'][res_gr_name]['force_dtype'] == channel_arr.dtype.str

                arr_view = channel_arr[...]
                if QUANTIZATION_DATA_DICT_ATTR_NAME in channel_arr.attrs:
                    data_dict = channel_arr.attrs[QUANTIZATION_DATA_DICT_ATTR_NAME]
                    data_dict["data"] = arr_view
                    arr_view = decode_quantized_data(data_dict)
                    if isinstance(arr_view, da.Array):
                        arr_view = arr_view.compute()

                mean_val = float(str(np.mean(arr_view)))
                std_val = float(str(np.std(arr_view)))
                max_val = float(str(arr_view.max()))
                min_val = float(str(arr_view.min()))

                sampling_info_dict.descriptive_statistics[res_gr_name][time_gr_name][
                    channel_arr_name
                ] = {
                    "mean": mean_val,
                    "std": std_val,
                    "max": max_val,
                    "min": min_val,
                }


def nii_volume_metadata_preprocessing(internal_volume: InternalVolume):
    root = open_zarr(
        internal_volume.path
    )

    source_db_name = internal_volume.entry_data.source_db_name
    source_db_id = internal_volume.entry_data.source_db_id
    # NOTE: sample nii has one channel
    channel_ids = [0]
    start_time = 0
    end_time = 0
    time_units = "millisecond"

    volume_downsamplings = get_downsamplings(data_group=root[VOLUME_DATA_GROUPNAME])

    source_axes_units = _get_source_axes_units(nii_header=internal_volume.map_header)
    metadata_dict = root.attrs["metadata_dict"]
    metadata_dict.entry_id.source_db_name = source_db_name
    metadata_dict.entry_id.source_db_id = source_db_id
    metadata_dict.volumes = VolumesMetadata(
        channel_ids=channel_ids,
        time_info=TimeInfo(
            kind="range", start=start_time, end=end_time, units=time_units
        ),
        sampling_info=VolumeSamplingInfo(
            spatial_downsampling_levels=volume_downsamplings,
            boxes={},
            descriptive_statistics={},
            time_transformations=[],
            source_axes_units=source_axes_units,
            original_axis_order=(0, 1, 2),
        ),
    )
    _get_nii_volume_sampling_info(
        root_data_group=root[VOLUME_DATA_GROUPNAME],
        sampling_info_dict=metadata_dict.volumes.sampling_info,
        nii_header=internal_volume.map_header,
        volume_downsamplings=volume_downsamplings,
    )

    root.attrs["metadata_dict"] = metadata_dict
    return metadata_dict
