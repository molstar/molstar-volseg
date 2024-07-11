import collections.abc
import json
import math
import re
from pathlib import Path
from typing import Union

import dask.array as da

import numpy as np
import zarr
from cellstar_db.models import (
    DatasetSpecificExtraData,
    DownsamplingLevelInfo,
    DownsamplingParams,
    Endianness,
    ExtraData,
    Metadata,
    ModeSFFDataType,
    OMETIFFSpecificExtraData,
    convert_to_angstroms,
)
from cellstar_preprocessor.flows.constants import METADATA_DICT_NAME, MIN_SIZE_PER_DOWNSAMPLING_LEVEL_MB, SHORT_UNIT_NAMES_TO_LONG
from cellstar_preprocessor.flows.zarr_methods import open_zarr

# from cellstar_db.file_system.constants import VOLUME_DATA_GROUPNAME
# from cellstar_preprocessor.model.segmentation import InternalSegmentation
# from cellstar_preprocessor.model.volume import InternalVolume


def _is_channels_correct(source_ometiff_metadata):
    ch = list(source_ometiff_metadata["Channels"].keys())
    number_of_channels = source_ometiff_metadata["SizeC"]
    if len(ch) != number_of_channels:
        return False
    else:
        return True



def _parse_ome_tiff_channel_id(ometiff_channel_id: str):
    channel_id = re.sub(r"\W+", "", ometiff_channel_id)
    return channel_id


# def set_ometiff_source_metadata(
#     int_vol_or_seg: InternalVolume | InternalSegmentation, metadata
# ):
#     if int_vol_or_seg.custom_data.dataset_specific_data is None:
#     #     if "ometiff" in int_vol_or_seg.custom_data["dataset_specific_data"]:
#     #         c: OMETIFFSpecificExtraData = int_vol_or_seg.custom_data[
#     #             "dataset_specific_data"
#     #         ]["ometiff"]
#     #         c["ometiff_source_metadata"] = metadata
#     #         int_vol_or_seg.custom_data["dataset_specific_data"]["ometiff"] = c
#     # else:
#         c = OMETIFFSpecificExtraData(ometiff_source_metadata=metadata)
#         # if 'dataset_specific_data' in int_vol_or_seg.custom_data
#         int_vol_or_seg.custom_data.dataset_specific_data = DatasetSpecificExtraData(ometiff=c
#         )


# def get_ometiff_source_metadata(int_vol_or_seg: InternalVolume | InternalSegmentation):
#     return int_vol_or_seg.custom_data["dataset_specific_data"]["ometiff"][
#         "ometiff_source_metadata"
#     ]


# for maps
def process_extra_data(path: Path, intermediate_zarr_structure: Path):
    data: ExtraData = read_json(path)
    zarr_structure: zarr.Group = open_zarr(intermediate_zarr_structure)
    zarr_structure.attrs["extra_data"] = data.model_dump()
    # NOTE: entry_metadata
    if data.entry_metadata is not None:
        metadata_dict: Metadata = Metadata.model_validate(
            zarr_structure.attrs[METADATA_DICT_NAME]
        )
        metadata_dict.entry_metadata = data.entry_metadata
        zarr_structure.attrs[METADATA_DICT_NAME] = metadata_dict


def update_dict(orig_dict, new_dict: dict):
    for key, val in new_dict.items():
        if isinstance(val, collections.abc.Mapping):
            tmp = update_dict(orig_dict.get(key, {}), val)
            orig_dict[key] = tmp
        # elif isinstance(val, list):
        #     orig_dict[key] = (orig_dict.get(key, []) + val)
        else:
            orig_dict[key] = new_dict[key]
    return orig_dict


# source: https://stackoverflow.com/a/11157531/13136429
def dictget(d, *k):
    """Get the values corresponding to the given keys in the provided dict."""
    return (d[i] for i in k)


def save_dict_to_json_file(d: dict | list, filename: str, path: Path) -> None:
    output_file = path / filename
    if not output_file.parent.exists():
        output_file.parent.mkdir(parents=True)

    with open(str((path / filename).resolve()), "w", encoding="utf-8") as fp:
        json.dump(d, fp, indent=4)


def read_json(path: Path):
    with open(path.resolve(), "r", encoding="utf-8") as f:
        # reads into dict
        read_file: dict | list = json.load(f)
    return read_file


def compute_downsamplings_to_be_stored(
    *,
    downsampling_parameters: DownsamplingParams,
    number_of_downsampling_steps: int,
    input_grid_size: int,
    dtype: np.dtype,
    factor: int,
):
    # if min_downsampling_level and max_downsampling_level are provided,
    # list between those two numbers
    lst = [2**i for i in range(1, number_of_downsampling_steps + 1)]
    if downsampling_parameters.max_downsampling_level:
        lst = [
            x
            for x in lst
            if x <= downsampling_parameters.max_downsampling_level
        ]
    if downsampling_parameters.min_downsampling_level:
        lst = [
            x
            for x in lst
            if x >= downsampling_parameters.min_downsampling_level
        ]
    if downsampling_parameters.max_size_per_downsampling_lvl_mb:
        x1_filesize_bytes: int = input_grid_size * dtype.itemsize
        # num_of_downsampling_step_to_start_saving_from
        n = math.ceil(
            math.log(
                x1_filesize_bytes
                / (
                    downsampling_parameters.max_size_per_downsampling_lvl_mb
                    * 1024**2
                ),
                factor,
            )
        )
        lst = [x for x in lst if x >= 2**n]
        if len(lst) == 0:
            raise Exception(
                f"No downsamplings will be saved: max size per channel {downsampling_parameters.max_size_per_downsampling_lvl_mb} is too low"
            )

    return lst


# TODO: should validate if min number of steps <= max number of steps
def compute_number_of_downsampling_steps(
    *,
    downsampling_parameters: DownsamplingParams,
    min_grid_size: int,
    input_grid_size: int,
    force_dtype: np.dtype,
    factor: int,
) -> int:
    num_of_downsampling_steps = 1
    # if this is set, set it to min
    if downsampling_parameters.min_downsampling_level is not None:
        num_of_downsampling_steps = int(
            math.log2(downsampling_parameters.min_downsampling_level)
        )
    # if this is set as well, set it to max
    if downsampling_parameters.max_downsampling_level is not None:
        num_of_downsampling_steps = int(
            math.log2(downsampling_parameters.max_downsampling_level)
        )

    # if neither of this set - calculate
    if (
        downsampling_parameters.max_downsampling_level is None
        and downsampling_parameters.min_downsampling_level is None
    ):
        if input_grid_size <= min_grid_size:
            return 1

        x1_filesize_bytes: int = input_grid_size * force_dtype.itemsize
        num_of_downsampling_steps = int(
            math.log(
                x1_filesize_bytes
                / (
                    MIN_SIZE_PER_DOWNSAMPLING_LEVEL_MB
                    * 10**6
                ),
                factor,
            )
        )
        if num_of_downsampling_steps <= 1:
            return 1

    return num_of_downsampling_steps


def decide_np_dtype(mode: ModeSFFDataType, endianness: Endianness):
    """decides np dtype based on mode (e.g. float32) and endianness (e.g. little) provided in SFF"""
    dt = np.dtype(mode.value)
    dt = dt.newbyteorder(endianness.value)
    return dt


def chunk_numpy_arr(arr: np.ndarray, chunk_size: int):
    lst = np.split(arr, np.arange(chunk_size, len(arr), chunk_size))
    return np.stack(lst, axis=0)

# def chunk_dask_arr(arr: da.Array, chunk_size: int):
#     lst = np.split(arr, np.arange(chunk_size, len(arr), chunk_size))
#     return np.stack(lst, axis=0)

def _convert_short_units_to_long(short_unit_name: str):
    # TODO: support conversion of other axes units (currently only µm to micrometer).
    # https://www.openmicroscopy.org/Schemas/Documentation/Generated/OME-2016-06/ome_xsd.html#Pixels_PhysicalSizeXUnit
    if short_unit_name in SHORT_UNIT_NAMES_TO_LONG:
        return SHORT_UNIT_NAMES_TO_LONG[short_unit_name]
    else:
        raise Exception("Short unit name is not supported")


# TODO: type annotation
def _get_ometiff_axes_units(ome_tiff_metadata):
    axes_units = {}
    if "PhysicalSizeXUnit" in ome_tiff_metadata:
        axes_units["x"] = _convert_short_units_to_long(
            ome_tiff_metadata["PhysicalSizeXUnit"]
        )
    else:
        axes_units["x"] = "angstrom"

    if "PhysicalSizeYUnit" in ome_tiff_metadata:
        axes_units["y"] = _convert_short_units_to_long(
            ome_tiff_metadata["PhysicalSizeYUnit"]
        )
    else:
        axes_units["y"] = "angstrom"

    if "PhysicalSizeZUnit" in ome_tiff_metadata:
        axes_units["z"] = _convert_short_units_to_long(
            ome_tiff_metadata["PhysicalSizeZUnit"]
        )
    else:
        axes_units["z"] = "angstrom"

    return axes_units


# def _get_ome_tiff_voxel_sizes_in_downsamplings(
#     internal_volume_or_segmentation: InternalVolume | InternalSegmentation,
#     boxes_dict,
#     downsamplings: list[DownsamplingLevelInfo],
#     ometiff_metadata,
# ):
#     ometiff_physical_size_dict: dict[str, str] = {}

#     # TODO: here check if internal_volume contains voxel_sizes
#     if "voxel_size" in internal_volume_or_segmentation.custom_data:
#         l = internal_volume_or_segmentation.custom_data.voxel_size
#         # if 'extra_data' in root.attrs:
#         #     # TODO: this is in micrometers
#         #     # we anyway do not support other units
#         #     l = root.attrs['extra_data']['scale_micron']
#         ometiff_physical_size_dict["x"] = l[0]
#         ometiff_physical_size_dict["y"] = l[1]
#         ometiff_physical_size_dict["z"] = l[2]
#     else:
#         # TODO: try to get from ometiff itself
#         ometiff_physical_size_dict = _get_ometiff_physical_size(ometiff_metadata)

#     ometiff_axes_units_dict = _get_ometiff_axes_units(ometiff_metadata)
#     # ometiff_physical_size_dict = _get_ometiff_physical_size(ometiff_metadata)

#     for info in downsamplings:
#         level = info["level"]
#         downsampling_level = str(level)
#         if downsampling_level == "1":
#             boxes_dict[downsampling_level].voxel_size = [
#                 convert_to_angstroms(
#                     ometiff_physical_size_dict["x"], ometiff_axes_units_dict["x"]
#                 ),
#                 convert_to_angstroms(
#                     ometiff_physical_size_dict["y"], ometiff_axes_units_dict["y"]
#                 ),
#                 convert_to_angstroms(
#                     ometiff_physical_size_dict["z"], ometiff_axes_units_dict["z"]
#                 ),
#             ]
#         else:
#             # NOTE: rounding error - if one of dimensions in original data is odd
#             boxes_dict[downsampling_level].voxel_size = [
#                 convert_to_angstroms(
#                     ometiff_physical_size_dict["x"] * int(downsampling_level),
#                     ometiff_axes_units_dict["x"],
#                 ),
#                 convert_to_angstroms(
#                     ometiff_physical_size_dict["y"] * int(downsampling_level),
#                     ometiff_axes_units_dict["y"],
#                 ),
#                 convert_to_angstroms(
#                     ometiff_physical_size_dict["z"] * int(downsampling_level),
#                     ometiff_axes_units_dict["z"],
#                 ),
#             ]


def _create_reorder_tuple(d: dict, correct_order: str):
    reorder_tuple = tuple([d[l] for l in correct_order])
    return reorder_tuple


def _get_missing_dims(sizesBF: list[int]):
    sizesBFcorrected = sizesBF[1:]
    missing = []
    order = "TZCYX"
    for idx, dim in enumerate(sizesBFcorrected):
        if dim == 1:
            missing.append(order[idx])
    print(f"Missing dims: {missing}")
    return missing


# def prepare_ometiff_for_writing(
#     img_array: da.Array, metadata, i: InternalVolume | InternalSegmentation
# ):
#     prepared_data: list[PreparedOMETIFFData] = []

#     d = {}
#     order = metadata["DimOrder BF Array"]
#     for letter in order:
#         d[str(letter)] = order.index(str(letter))

#     missing_dims = []

#     if len(img_array.shape) != 5:
#         missing_dims = _get_missing_dims(metadata["Sizes BF"])
#         for missing_dim in missing_dims:
#             img_array = da.expand_dims(img_array, axis=d[missing_dim])

#     CORRECT_ORDER = "TCXYZ"
#     reorder_tuple = _create_reorder_tuple(d, CORRECT_ORDER)
#     # NOTE: assumes correct order is TCXYZ

#     i.custom_data

#     rearranged_arr = img_array.transpose(*reorder_tuple)

#     artificial_channel_ids = list(range(rearranged_arr.shape[1]))
#     artificial_channel_ids = [str(x) for x in artificial_channel_ids]
#     # TODO: prepare list of of PreparedOMETIFFData
#     # for each time and channel
#     for time in range(rearranged_arr.shape[0]):
#         time_arr = rearranged_arr[time]
#         for channel_number in range(time_arr.shape[0]):
#             three_d_arr = time_arr[channel_number]
#             p = PreparedOMETIFFData(
#                 channel_number=channel_number,
#                 timeframe_index=time,
#                 data=three_d_arr,
#             )
#             prepared_data.append(p)

#     artificial_channel_ids_dict = dict(
#         zip(artificial_channel_ids, artificial_channel_ids)
#     )
#     return prepared_data, artificial_channel_ids_dict


def get_ome_tiff_origins(boxes_dict: dict, downsamplings: list[DownsamplingLevelInfo]):
    # NOTE: origins seem to be 0, 0, 0, as they are not specified
    available = list(filter(lambda a: a["available"] == True, downsamplings))
    downsampling_levels = sorted([a["level"] for a in available])
    for level in downsampling_levels:
        downsampling_level = str(level)
        boxes_dict[downsampling_level].origin = [0, 0, 0]
