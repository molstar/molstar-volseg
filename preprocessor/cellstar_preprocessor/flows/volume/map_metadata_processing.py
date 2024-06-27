from decimal import ROUND_CEILING, Decimal, getcontext

import dask.array as da
import numpy as np
from cellstar_db.models import (
    DownsamplingLevelInfo,
    TimeInfo,
    VolumeSamplingInfo,
    VolumesMetadata,
)
from cellstar_preprocessor.flows.common import (
    get_downsamplings,
    open_zarr_structure_from_path,
)
from cellstar_preprocessor.flows.constants import (
    QUANTIZATION_DATA_DICT_ATTR_NAME,
    VOLUME_DATA_GROUPNAME,
)
from cellstar_preprocessor.model.volume import InternalVolume
from cellstar_preprocessor.tools.quantize_data.quantize_data import (
    decode_quantized_data,
)


def _get_axis_order_mrcfile(mrc_header: object):
    h = mrc_header
    current_order = int(h.mapc) - 1, int(h.mapr) - 1, int(h.maps) - 1
    return current_order


def _ccp4_words_to_dict_mrcfile(mrc_header: object) -> dict:
    """input - mrcfile object header (mrc.header)"""
    ctx = getcontext()
    ctx.rounding = ROUND_CEILING
    d = {}

    m = mrc_header
    # mrcfile implementation
    d["NC"], d["NR"], d["NS"] = int(m.nx), int(m.ny), int(m.nz)
    d["NCSTART"], d["NRSTART"], d["NSSTART"] = (
        int(m.nxstart),
        int(m.nystart),
        int(m.nzstart),
    )
    d["xLength"] = round(Decimal(float(m.cella.x)), 5)
    d["yLength"] = round(Decimal(float(m.cella.y)), 5)
    d["zLength"] = round(Decimal(float(m.cella.z)), 5)
    d["MAPC"], d["MAPR"], d["MAPS"] = int(m.mapc), int(m.mapr), int(m.maps)

    return d


def _get_origin_and_voxel_sizes_from_map_header(
    mrc_header: object, volume_downsamplings: list[DownsamplingLevelInfo]
):
    d = _ccp4_words_to_dict_mrcfile(mrc_header)
    ao = {d["MAPC"] - 1: 0, d["MAPR"] - 1: 1, d["MAPS"] - 1: 2}

    N = d["NC"], d["NR"], d["NS"]
    N = N[ao[0]], N[ao[1]], N[ao[2]]

    START = d["NCSTART"], d["NRSTART"], d["NSSTART"]
    START = START[ao[0]], START[ao[1]], START[ao[2]]

    original_voxel_size: tuple[float, float, float] = (
        d["xLength"] / N[0],
        d["yLength"] / N[1],
        d["zLength"] / N[2],
    )

    voxel_sizes_in_downsamplings: dict = {}
    for level in volume_downsamplings:
        rate = level["level"]
        voxel_sizes_in_downsamplings[rate] = tuple(
            [float(Decimal(i) * Decimal(rate)) for i in original_voxel_size]
        )

    # get origin of grid based on NC/NR/NSSTART variables (5, 6, 7) and original voxel size
    # Converting to strings, then to floats to make it JSON serializable (decimals are not) -> ??
    origin: tuple[float, float, float] = (
        float(str(START[0] * original_voxel_size[0])),
        float(str(START[1] * original_voxel_size[1])),
        float(str(START[2] * original_voxel_size[2])),
    )

    return origin, voxel_sizes_in_downsamplings


def _get_volume_sampling_info(
    root_data_group,
    sampling_info_dict,
    mrc_header: object,
    volume_downsamplings: list[VolumeSamplingInfo],
):
    # TODO: modify it such that voxel sizes are calculated on each iteration
    origin, voxel_sizes_in_downsamplings = _get_origin_and_voxel_sizes_from_map_header(
        mrc_header=mrc_header, volume_downsamplings=volume_downsamplings
    )
    for res_gr_name, res_gr in root_data_group.groups():
        # create layers (time gr, channel gr)
        sampling_info_dict["boxes"][res_gr_name] = {
            "origin": origin,
            "voxel_size": voxel_sizes_in_downsamplings[int(res_gr_name)],
            "grid_dimensions": None,
            # 'force_dtype': None
        }

        sampling_info_dict["descriptive_statistics"][res_gr_name] = {}

        for time_gr_name, time_gr in res_gr.groups():
            first_group_key = sorted(time_gr.array_keys())[0]

            sampling_info_dict["boxes"][res_gr_name]["grid_dimensions"] = time_gr[
                first_group_key
            ].shape
            # sampling_info_dict['boxes'][res_gr_name]['force_dtype'] = time_gr[first_group_key].dtype.str

            sampling_info_dict["descriptive_statistics"][res_gr_name][time_gr_name] = {}
            for channel_arr_name, channel_arr in time_gr.arrays():
                assert (
                    sampling_info_dict["boxes"][res_gr_name]["grid_dimensions"]
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

                sampling_info_dict["descriptive_statistics"][res_gr_name][time_gr_name][
                    channel_arr_name
                ] = {
                    "mean": mean_val,
                    "std": std_val,
                    "max": max_val,
                    "min": min_val,
                }


def map_metadata_processing(internal_volume: InternalVolume):
    root = open_zarr_structure_from_path(
        internal_volume.intermediate_zarr_structure_path
    )
    source_db_name = internal_volume.entry_data.source_db_name
    source_db_id = internal_volume.entry_data.source_db_id
    # map has one channel
    channel_ids = [0]
    start_time = 0
    end_time = 0
    time_units = "millisecond"

    map_header = internal_volume.map_header

    volume_downsamplings = get_downsamplings(data_group=root[VOLUME_DATA_GROUPNAME])
    # TODO: check - some units are defined (spatial?)
    source_axes_units = {}
    metadata_dict = root.attrs["metadata_dict"]
    metadata_dict["entry_id"]["source_db_name"] = source_db_name
    metadata_dict["entry_id"]["source_db_id"] = source_db_id
    metadata_dict["volumes"] = VolumesMetadata(
        channel_ids=channel_ids,
        time_info=TimeInfo(
            kind="range", start=start_time, end=end_time, units=time_units
        ),
        volume_sampling_info=VolumeSamplingInfo(
            spatial_downsampling_levels=volume_downsamplings,
            boxes={},
            descriptive_statistics={},
            time_transformations=[],
            source_axes_units=source_axes_units,
            original_axis_order=_get_axis_order_mrcfile(map_header),
        ),
    )

    _get_volume_sampling_info(
        root_data_group=root[VOLUME_DATA_GROUPNAME],
        sampling_info_dict=metadata_dict["volumes"]["volume_sampling_info"],
        mrc_header=map_header,
        volume_downsamplings=volume_downsamplings,
    )

    # NOTE: remove original level resolution data
    if internal_volume.downsampling_parameters.remove_original_resolution:
        del root[VOLUME_DATA_GROUPNAME]["1"]
        print("Original resolution volume data removed")

        current_levels: list[DownsamplingLevelInfo] = metadata_dict["volumes"][
            "volume_sampling_info"
        ]["spatial_downsampling_levels"]
        for i, item in enumerate(current_levels):
            if item["level"] == 1:
                current_levels[i]["available"] = False

        metadata_dict["volumes"]["volume_sampling_info"][
            "spatial_downsampling_levels"
        ] = current_levels

    root.attrs["metadata_dict"] = metadata_dict

    return metadata_dict
