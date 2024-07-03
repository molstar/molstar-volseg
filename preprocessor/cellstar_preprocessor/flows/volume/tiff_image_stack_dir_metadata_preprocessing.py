from decimal import Decimal

from cellstar_preprocessor.flows.volume.map_volume_metadata_preprocessing import map_volume_metadata_preprocessing
import dask.array as da
import zarr
from cellstar_db.models import (
    DownsamplingLevelInfo,
    TimeInfo,
    VolumeSamplingInfo,
    VolumesMetadata,
)

from cellstar_preprocessor.flows.constants import VOLUME_DATA_GROUPNAME
from cellstar_preprocessor.model.volume import InternalVolume

SHORT_UNIT_NAMES_TO_LONG = {
    "µm": "micrometer",
    # TODO: support other units
}


# def _get_source_axes_units():
#     # NOTE: hardcoding this for now
#     spatial_units = "micrometer"
#     d = {"x": spatial_units, "y": spatial_units, "z": spatial_units}
#     # d = {}
#     return d


# def _convert_short_units_to_long(short_unit_name: str):
#     # TODO: support conversion of other axes units (currently only µm to micrometer).
#     # https://www.openmicroscopy.org/Schemas/Documentation/Generated/OME-2016-06/ome_xsd.html#Pixels_PhysicalSizeXUnit
#     if short_unit_name in SHORT_UNIT_NAMES_TO_LONG:
#         return SHORT_UNIT_NAMES_TO_LONG[short_unit_name]
#     else:
#         raise Exception("Short unit name is not supported")


# def _get_ometiff_physical_size(ome_tiff_metadata):
#     d = {}
#     if "PhysicalSizeX" in ome_tiff_metadata:
#         d["x"] = ome_tiff_metadata["PhysicalSizeX"]
#     else:
#         d["x"] = 1.0

#     if "PhysicalSizeY" in ome_tiff_metadata:
#         d["y"] = ome_tiff_metadata["PhysicalSizeY"]
#     else:
#         d["y"] = 1.0

#     if "PhysicalSizeZ" in ome_tiff_metadata:
#         d["z"] = ome_tiff_metadata["PhysicalSizeZ"]
#     else:
#         d["z"] = 1.0

#     return d


# def _get_segmentation_sampling_info(root_data_group, sampling_info_dict):
#     for res_gr_name, res_gr in root_data_group.groups():
#         # create layers (time gr, channel gr)
#         sampling_info_dict["boxes"][res_gr_name] = {
#             "origin": None,
#             "voxel_size": None,
#             "grid_dimensions": None,
#             # 'force_dtype': None
#         }

#         for time_gr_name, time_gr in res_gr.groups():
#             sampling_info_dict["boxes"][res_gr_name][
#                 "grid_dimensions"
#             ] = time_gr.grid.shape


# def _get_ometiff_axes_units(ome_tiff_metadata):
#     axes_units = {}
#     if "PhysicalSizeXUnit" in ome_tiff_metadata:
#         axes_units["x"] = _convert_short_units_to_long(
#             ome_tiff_metadata["PhysicalSizeXUnit"]
#         )
#     else:
#         axes_units["x"] = "micrometer"

#     if "PhysicalSizeYUnit" in ome_tiff_metadata:
#         axes_units["y"] = _convert_short_units_to_long(
#             ome_tiff_metadata["PhysicalSizeYUnit"]
#         )
#     else:
#         axes_units["y"] = "micrometer"

#     if "PhysicalSizeZUnit" in ome_tiff_metadata:
#         axes_units["z"] = _convert_short_units_to_long(
#             ome_tiff_metadata["PhysicalSizeZUnit"]
#         )
#     else:
#         axes_units["z"] = "micrometer"

#     return axes_units


def _get_voxel_sizes_in_downsamplings(
    original_voxel_size: list[float, float, float],
    volume_downsamplings: list[DownsamplingLevelInfo],
):
    voxel_sizes_in_downsamplings: dict = {}
    for level in volume_downsamplings:
        rate = level["level"]
        voxel_sizes_in_downsamplings[rate] = tuple(
            [float(Decimal(float(i)) * Decimal(rate)) for i in original_voxel_size]
        )
    return voxel_sizes_in_downsamplings


def _get_volume_sampling_info(
    root_data_group: zarr.Group, sampling_info_dict, internal_volume: InternalVolume
):
    volume_downsamplings = get_downsamplings(root_data_group)
    if "voxel_size" in internal_volume.custom_data:
        voxel_sizes_in_downsamplings = _get_voxel_sizes_in_downsamplings(
            internal_volume.custom_data["voxel_size"], volume_downsamplings
        )
    else:
        raise Exception(
            "Voxel size should be specified for TIFF stack image processing"
        )

    for res_gr_name, res_gr in root_data_group.groups():
        # create layers (time gr, channel gr)
        sampling_info_dict["boxes"][res_gr_name] = {
            "origin": [0, 0, 0],
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

                # trying to get arr view takes long
                # arr_view = channel_arr[...]
                arr_view: da.Array = da.from_zarr(channel_arr)
                # if QUANTIZATION_DATA_DICT_ATTR_NAME in arr.attrs:
                #     data_dict = arr.attrs[QUANTIZATION_DATA_DICT_ATTR_NAME]
                #     data_dict['data'] = arr_view
                #     arr_view = decode_quantized_data(data_dict)
                #     if isinstance(arr_view, da.Array):
                #         arr_view = arr_view.compute()

                mean_val = float(str(arr_view.mean().compute()))
                std_val = float(str(arr_view.std().compute()))
                max_val = float(str(arr_view.max().compute()))
                min_val = float(str(arr_view.min().compute()))

                sampling_info_dict["descriptive_statistics"][res_gr_name][time_gr_name][
                    channel_arr_name
                ] = {
                    "mean": mean_val,
                    "std": std_val,
                    "max": max_val,
                    "min": min_val,
                }


# def _get_allencell_image_channel_ids(root: zarr.Group):
#     return root.attrs["extra_data"]["name_dict"]["crop_raw"]


# def _get_allencell_voxel_size(root: zarr.Group) -> list[float, float, float]:
#     return root.attrs["extra_data"]["scale_micron"]


def tiff_image_stack_dir_metadata_preprocessing(v: InternalVolume):
    map_volume_metadata_preprocessing(v)
    # # same as for volumes?
    # root = open_zarr_structure_from_path(
    #     i.intermediate_zarr_structure_path
    # )

    # source_db_name = i.entry_data.source_db_name
    # source_db_id = i.entry_data.source_db_id

    # start_time = 0
    # end_time = 0
    # time_units = "millisecond"

    # volume_downsamplings = get_downsamplings(data_group=root[VOLUME_DATA_GROUPNAME])

    # # TODO:
    # source_axes_units = {}

    # metadata_dict = root.attrs["metadata_dict"]
    # metadata_dict["entry_id"]["source_db_name"] = source_db_name
    # metadata_dict["entry_id"]["source_db_id"] = source_db_id

    # channel_ids = ["0"]

    # metadata_dict["volumes"] = VolumesMetadata(
    #     channel_ids=channel_ids,
    #     time_info=TimeInfo(
    #         kind="range", start=start_time, end=end_time, units=time_units
    #     ),
    #     volume_sampling_info=VolumeSamplingInfo(
    #         spatial_downsampling_levels=volume_downsamplings,
    #         boxes={},
    #         descriptive_statistics={},
    #         time_transformations=[],
    #         source_axes_units=source_axes_units,
    #         original_axis_order=(0, 1, 2),
    #     ),
    # )
    # _get_volume_sampling_info(
    #     root_data_group=root[VOLUME_DATA_GROUPNAME],
    #     sampling_info_dict=metadata_dict["volumes"]["volume_sampling_info"],
    #     internal_volume=i,
    # )

    # # _get_ome_tiff_voxel_sizes_in_downsamplings(
    # #     internal_volume_or_segmentation=internal_volume,
    # #     boxes_dict=metadata_dict["volumes"]["volume_sampling_info"]["boxes"],
    # #     downsamplings=volume_downsamplings,
    # #     ometiff_metadata=ometiff_metadata,
    # # )
    # # _get_allencell_voxel_sizes_in_downsamplings(
    # #     boxes_dict=metadata_dict['volumes']['volume_sampling_info']['boxes'],
    # #     downsamplings=volume_downsamplings,
    # #     original_voxel_size_in_micrometers=original_voxel_size_in_micrometers
    # # )

    # # TODO: get origins
    # # get_ome_tiff_origins(
    # #     boxes_dict=metadata_dict["volumes"]["volume_sampling_info"]["boxes"],
    # #     downsamplings=volume_downsamplings,
    # # )

    # root.attrs["metadata_dict"] = metadata_dict
    # return metadata_dict
