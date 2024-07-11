from cellstar_preprocessor.flows.volume.map_volume_metadata_preprocessing import map_volume_metadata_preprocessing
import dask.array as da
import zarr
from cellstar_db.models import (
    OMETIFFSpecificExtraData,
    TimeInfo,
    VolumeSamplingInfo,
    VolumesMetadata,
)
from cellstar_preprocessor.flows.constants import DEFAULT_TIME_UNITS, VOLUME_DATA_GROUPNAME
from cellstar_preprocessor.flows.zarr_methods import get_downsamplings, open_zarr
from cellstar_preprocessor.model.volume import InternalVolume

SHORT_UNIT_NAMES_TO_LONG = {
    "µm": "micrometer",
    # TODO: support other units
}


def _get_source_axes_units():
    # NOTE: hardcoding this for now
    spatial_units = "micrometer"
    d = {"x": spatial_units, "y": spatial_units, "z": spatial_units}
    # d = {}
    return d


def _convert_short_units_to_long(short_unit_name: str):
    # TODO: support conversion of other axes units (currently only µm to micrometer).
    # https://www.openmicroscopy.org/Schemas/Documentation/Generated/OME-2016-06/ome_xsd.html#Pixels_PhysicalSizeXUnit
    if short_unit_name in SHORT_UNIT_NAMES_TO_LONG:
        return SHORT_UNIT_NAMES_TO_LONG[short_unit_name]
    else:
        raise Exception("Short unit name is not supported")


def _get_ometiff_physical_size(ome_tiff_metadata):
    d = {}
    if "PhysicalSizeX" in ome_tiff_metadata:
        d["x"] = ome_tiff_metadata["PhysicalSizeX"]
    else:
        d["x"] = 1.0

    if "PhysicalSizeY" in ome_tiff_metadata:
        d["y"] = ome_tiff_metadata["PhysicalSizeY"]
    else:
        d["y"] = 1.0

    if "PhysicalSizeZ" in ome_tiff_metadata:
        d["z"] = ome_tiff_metadata["PhysicalSizeZ"]
    else:
        d["z"] = 1.0

    return d


def _get_volume_sampling_info(root_data_group: zarr.Group, sampling_info_dict):
    for res_gr_name, res_gr in root_data_group.groups():
        # create layers (time gr, channel gr)
        sampling_info_dict.boxes[res_gr_name] = {
            "origin": None,
            "voxel_size": None,
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

                sampling_info_dict.descriptive_statistics[res_gr_name][time_gr_name][
                    channel_arr_name
                ] = {
                    "mean": mean_val,
                    "std": std_val,
                    "max": max_val,
                    "min": min_val,
                }


def _get_allencell_image_channel_ids(root: zarr.Group):
    return root.attrs["extra_data"]["name_dict"]["crop_raw"]


def _get_allencell_voxel_size(root: zarr.Group) -> list[float, float, float]:
    return root.attrs["extra_data"]["scale_micron"]


def ometiff_volume_metadata_preprocessing(v: InternalVolume):
    map_volume_metadata_preprocessing(v)