import collections.abc
import gc
import json
import math
import re
from pathlib import Path
from typing import TypedDict, Union

import dask.array as da
import numpy as np
import zarr
from cellstar_db.models import (
    ChannelAnnotation,
    DownsamplingLevelInfo,
    ExtraData,
    Metadata,
    OMETIFFSpecificExtraData,
)
from cellstar_preprocessor.flows.constants import (
    SHORT_UNIT_NAMES_TO_LONG,
    SPACE_UNITS_CONVERSION_DICT,
)
from cellstar_preprocessor.model.segmentation import InternalSegmentation
from cellstar_preprocessor.model.volume import InternalVolume
from PIL import ImageColor
from pyometiff import OMETIFFReader


def _is_channels_correct(source_ometiff_metadata):
    ch = list(source_ometiff_metadata["Channels"].keys())
    number_of_channels = source_ometiff_metadata["SizeC"]
    if len(ch) != number_of_channels:
        return False
    else:
        return True


def _get_ome_tiff_channel_ids_dict(root: zarr.Group, internal_volume: InternalVolume):
    return internal_volume.custom_data["channel_ids_mapping"]


def _parse_ome_tiff_channel_id(ometiff_channel_id: str):
    channel_id = re.sub(r"\W+", "", ometiff_channel_id)
    return channel_id


def set_ometiff_source_metadata(
    int_vol_or_seg: InternalVolume | InternalSegmentation, metadata
):
    if "dataset_specific_data" in int_vol_or_seg.custom_data:
        if "ometiff" in int_vol_or_seg.custom_data["dataset_specific_data"]:
            c: OMETIFFSpecificExtraData = int_vol_or_seg.custom_data[
                "dataset_specific_data"
            ]["ometiff"]
            c["ometiff_source_metadata"] = metadata
            int_vol_or_seg.custom_data["dataset_specific_data"]["ometiff"] = c
    else:
        c: OMETIFFSpecificExtraData = {"ometiff_source_metadata": metadata}
        # if 'dataset_specific_data' in int_vol_or_seg.custom_data
        try:
            int_vol_or_seg.custom_data["dataset_specific_data"]["ometiff"] = c
        except KeyError:
            int_vol_or_seg.custom_data["dataset_specific_data"] = {"ometiff": c}


def get_ometiff_source_metadata(int_vol_or_seg: InternalVolume | InternalSegmentation):
    return int_vol_or_seg.custom_data["dataset_specific_data"]["ometiff"][
        "ometiff_source_metadata"
    ]


def set_volume_custom_data(internal_volume: InternalVolume, zarr_structure: zarr.Group):
    if "extra_data" in zarr_structure.attrs:
        if "volume" in zarr_structure.attrs["extra_data"]:
            internal_volume.custom_data = zarr_structure.attrs["extra_data"]["volume"]
        else:
            internal_volume.custom_data = {}
    else:
        internal_volume.custom_data = {}


def set_segmentation_custom_data(
    internal_segmentation: InternalSegmentation, zarr_structure: zarr.Group
):
    if "extra_data" in zarr_structure.attrs:
        if "segmentation" in zarr_structure.attrs["extra_data"]:
            internal_segmentation.custom_data = zarr_structure.attrs["extra_data"][
                "segmentation"
            ]
        else:
            internal_segmentation.custom_data = {}
    else:
        internal_segmentation.custom_data = {}


def process_extra_data(path: Path, intermediate_zarr_structure: Path):
    data: ExtraData = open_json_file(path)
    zarr_structure: zarr.Group = open_zarr_structure_from_path(
        intermediate_zarr_structure
    )
    zarr_structure.attrs["extra_data"] = data
    # NOTE: entry_metadata
    if "entry_metadata" in data:
        metadata_dict: Metadata = zarr_structure.attrs["metadata_dict"]
        metadata_dict["entry_metadata"] = data["entry_metadata"]
        zarr_structure.attrs["metadata_dict"] = metadata_dict


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


def get_downsamplings(data_group: zarr.Group) -> list[DownsamplingLevelInfo]:
    downsamplings = []
    for gr_name, gr in data_group.groups():
        downsamplings.append(gr_name)
        downsamplings = sorted(downsamplings)

    # convert to ints
    downsamplings = sorted([int(x) for x in downsamplings])
    downsampling_info_list: list[DownsamplingLevelInfo] = []
    for downsampling in downsamplings:
        info: DownsamplingLevelInfo = {"available": True, "level": downsampling}
        downsampling_info_list.append(info)

    return downsampling_info_list


def save_dict_to_json_file(d: dict | list, filename: str, path: Path) -> None:
    output_file = path / filename
    if not output_file.parent.exists():
        output_file.parent.mkdir(parents=True)

    with open(str((path / filename).resolve()), "w", encoding="utf-8") as fp:
        json.dump(d, fp, indent=4)


def open_json_file(path: Path):
    with open(path.resolve(), "r", encoding="utf-8") as f:
        # reads into dict
        read_file: dict | list = json.load(f)
    return read_file


def compute_downsamplings_to_be_stored(
    *,
    int_vol_or_seg: Union[InternalVolume, InternalSegmentation],
    number_of_downsampling_steps: int,
    input_grid_size: int,
    dtype: np.dtype,
    factor: int,
):
    # if min_downsampling_level and max_downsampling_level are provided,
    # list between those two numbers
    lst = [2**i for i in range(1, number_of_downsampling_steps + 1)]
    if int_vol_or_seg.downsampling_parameters.max_downsampling_level:
        lst = [
            x
            for x in lst
            if x <= int_vol_or_seg.downsampling_parameters.max_downsampling_level
        ]
    if int_vol_or_seg.downsampling_parameters.min_downsampling_level:
        lst = [
            x
            for x in lst
            if x >= int_vol_or_seg.downsampling_parameters.min_downsampling_level
        ]
    if int_vol_or_seg.downsampling_parameters.max_size_per_downsampling_lvl_mb:
        x1_filesize_bytes: int = input_grid_size * dtype.itemsize
        # num_of_downsampling_step_to_start_saving_from
        n = math.ceil(
            math.log(
                x1_filesize_bytes
                / (
                    int_vol_or_seg.downsampling_parameters.max_size_per_downsampling_lvl_mb
                    * 1024**2
                ),
                factor,
            )
        )
        lst = [x for x in lst if x >= 2**n]
        if len(lst) == 0:
            raise Exception(
                f"No downsamplings will be saved: max size per channel {int_vol_or_seg.downsampling_parameters.max_size_per_downsampling_lvl_mb} is too low"
            )

    return lst


# TODO: should validate if min number of steps <= max number of steps
def compute_number_of_downsampling_steps(
    *,
    int_vol_or_seg: Union[InternalVolume, InternalSegmentation],
    min_grid_size: int,
    input_grid_size: int,
    force_dtype: np.dtype,
    factor: int,
) -> int:
    num_of_downsampling_steps = 1
    # if this is set, set it to min
    if int_vol_or_seg.downsampling_parameters.min_downsampling_level:
        num_of_downsampling_steps = int(
            math.log2(int_vol_or_seg.downsampling_parameters.min_downsampling_level)
        )
    # if this is set as well, set it to max
    if int_vol_or_seg.downsampling_parameters.max_downsampling_level:
        num_of_downsampling_steps = int(
            math.log2(int_vol_or_seg.downsampling_parameters.max_downsampling_level)
        )

    # if neither of this set - calculate
    if (
        not int_vol_or_seg.downsampling_parameters.max_downsampling_level
        and not int_vol_or_seg.downsampling_parameters.min_downsampling_level
    ):
        if input_grid_size <= min_grid_size:
            return 1

        x1_filesize_bytes: int = input_grid_size * force_dtype.itemsize
        num_of_downsampling_steps = int(
            math.log(
                x1_filesize_bytes
                / (
                    int_vol_or_seg.downsampling_parameters.min_size_per_downsampling_lvl_mb
                    * 10**6
                ),
                factor,
            )
        )
        if num_of_downsampling_steps <= 1:
            return 1

    return num_of_downsampling_steps


def _compute_chunk_size_based_on_data(arr: np.ndarray) -> tuple[int, int, int]:
    shape: tuple = arr.shape
    chunks = tuple([int(i / 4) if i > 4 else i for i in shape])
    return chunks


def open_zarr_zip(path: Path) -> zarr.Group:
    store = zarr.ZipStore(path=path, compression=0, allowZip64=True, mode="r")
    # Re-create zarr hierarchy from opened store
    root: zarr.Group = zarr.group(store=store)
    return root


def open_zarr_structure_from_path(path: Path) -> zarr.Group:
    store: zarr.storage.DirectoryStore = zarr.DirectoryStore(str(path))
    # Re-create zarr hierarchy from opened store
    root: zarr.Group = zarr.group(store=store)
    return root


def create_dataset_wrapper(
    zarr_group: zarr.Group,
    data,
    name,
    shape,
    dtype,
    params_for_storing: dict,
    is_empty=False,
) -> zarr.core.Array:
    compressor = params_for_storing.compressor
    chunking_mode = params_for_storing.chunking_mode

    if chunking_mode == "auto":
        chunks = True
    elif chunking_mode == "custom_function":
        chunks = _compute_chunk_size_based_on_data(data)
    elif chunking_mode == "false":
        chunks = False
    else:
        raise ValueError(f"Chunking approach arg value is invalid: {chunking_mode}")
    if not is_empty:
        zarr_arr = zarr_group.create_dataset(
            data=data,
            name=name,
            shape=shape,
            dtype=dtype,
            compressor=compressor,
            chunks=chunks,
        )
    else:
        zarr_arr = zarr_group.create_dataset(
            name=name, shape=shape, dtype=dtype, compressor=compressor, chunks=chunks
        )

    return zarr_arr


def decide_np_dtype(mode: str, endianness: str):
    """decides np dtype based on mode (e.g. float32) and endianness (e.g. little) provided in SFF"""
    dt = np.dtype(mode)
    dt = dt.newbyteorder(endianness)
    return dt


def chunk_numpy_arr(arr, chunk_size):
    lst = np.split(arr, np.arange(chunk_size, len(arr), chunk_size))
    return np.stack(lst, axis=0)


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


def _convert_to_angstroms(value, input_unit: str):
    # TODO: support other units
    if input_unit in SPACE_UNITS_CONVERSION_DICT:
        return value * SPACE_UNITS_CONVERSION_DICT[input_unit]
    else:
        raise Exception(f"{input_unit} space unit is not supported")


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


def _get_ome_tiff_voxel_sizes_in_downsamplings(
    internal_volume_or_segmentation: InternalVolume | InternalSegmentation,
    boxes_dict,
    downsamplings: list[DownsamplingLevelInfo],
    ometiff_metadata,
):
    ometiff_physical_size_dict: dict[str, str] = {}

    # TODO: here check if internal_volume contains voxel_sizes
    if "voxel_size" in internal_volume_or_segmentation.custom_data:
        l = internal_volume_or_segmentation.custom_data["voxel_size"]
        # if 'extra_data' in root.attrs:
        #     # TODO: this is in micrometers
        #     # we anyway do not support other units
        #     l = root.attrs['extra_data']['scale_micron']
        ometiff_physical_size_dict["x"] = l[0]
        ometiff_physical_size_dict["y"] = l[1]
        ometiff_physical_size_dict["z"] = l[2]
    else:
        # TODO: try to get from ometiff itself
        ometiff_physical_size_dict = _get_ometiff_physical_size(ometiff_metadata)

    ometiff_axes_units_dict = _get_ometiff_axes_units(ometiff_metadata)
    # ometiff_physical_size_dict = _get_ometiff_physical_size(ometiff_metadata)

    for info in downsamplings:
        level = info["level"]
        downsampling_level = str(level)
        if downsampling_level == "1":
            boxes_dict[downsampling_level]["voxel_size"] = [
                _convert_to_angstroms(
                    ometiff_physical_size_dict["x"], ometiff_axes_units_dict["x"]
                ),
                _convert_to_angstroms(
                    ometiff_physical_size_dict["y"], ometiff_axes_units_dict["y"]
                ),
                _convert_to_angstroms(
                    ometiff_physical_size_dict["z"], ometiff_axes_units_dict["z"]
                ),
            ]
        else:
            # NOTE: rounding error - if one of dimensions in original data is odd
            boxes_dict[downsampling_level]["voxel_size"] = [
                _convert_to_angstroms(
                    ometiff_physical_size_dict["x"] * int(downsampling_level),
                    ometiff_axes_units_dict["x"],
                ),
                _convert_to_angstroms(
                    ometiff_physical_size_dict["y"] * int(downsampling_level),
                    ometiff_axes_units_dict["y"],
                ),
                _convert_to_angstroms(
                    ometiff_physical_size_dict["z"] * int(downsampling_level),
                    ometiff_axes_units_dict["z"],
                ),
            ]


def read_ometiff_to_dask(int_vol_or_seg: InternalVolume | InternalSegmentation):
    if isinstance(int_vol_or_seg, InternalVolume):
        fpath = int_vol_or_seg.input_path
    else:
        fpath = int_vol_or_seg.input_path
    reader = OMETIFFReader(fpath=fpath)
    img_array_np, metadata, xml_metadata = reader.read()
    img_array = da.from_array(img_array_np)
    del img_array_np
    gc.collect()
    return img_array, metadata, xml_metadata


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


class PreparedOMETIFFData(TypedDict):
    time: int
    # channel would be int
    # TODO: get its name later on
    channel_number: int
    data: np.ndarray


def prepare_ometiff_for_writing(
    img_array: da.Array, metadata, int_vol_or_seg: InternalVolume | InternalSegmentation
):
    prepared_data: list[PreparedOMETIFFData] = []

    d = {}
    order = metadata["DimOrder BF Array"]
    for letter in order:
        d[str(letter)] = order.index(str(letter))

    missing_dims = []

    if len(img_array.shape) != 5:
        local_d = {"T": 0, "Z": 1, "C": 2, "Y": 3, "X": 4}
        missing_dims = _get_missing_dims(metadata["Sizes BF"])
        for missing_dim in missing_dims:
            img_array = da.expand_dims(img_array, axis=local_d[missing_dim])

        d = local_d

    CORRECT_ORDER = "TCXYZ"
    reorder_tuple = _create_reorder_tuple(d, CORRECT_ORDER)
    # NOTE: assumes correct order is TCXYZ

    int_vol_or_seg.custom_data

    rearranged_arr = img_array.transpose(*reorder_tuple)

    artificial_channel_ids = list(range(rearranged_arr.shape[1]))
    artificial_channel_ids = [str(x) for x in artificial_channel_ids]
    # TODO: prepare list of of PreparedOMETIFFData
    # for each time and channel
    for time in range(rearranged_arr.shape[0]):
        time_arr = rearranged_arr[time]
        for channel_number in range(time_arr.shape[0]):
            three_d_arr = time_arr[channel_number]
            p: PreparedOMETIFFData = {
                "channel_number": channel_number,
                "time": time,
                "data": three_d_arr,
            }
            prepared_data.append(p)

    artificial_channel_ids_dict = dict(
        zip(artificial_channel_ids, artificial_channel_ids)
    )
    return prepared_data, artificial_channel_ids_dict


def hex_to_rgba_normalized(channel_color_hex):
    channel_color_rgba = ImageColor.getcolor(f"#{channel_color_hex}", "RGBA")
    channel_color_rgba_fractional = tuple([i / 255 for i in channel_color_rgba])
    return channel_color_rgba_fractional


def get_channel_annotations(ome_zarr_attrs: dict):
    volume_channel_annotations: list[ChannelAnnotation] = []
    for channel_id, channel in enumerate(ome_zarr_attrs["omero"]["channels"]):
        label = None if not channel["label"] else channel["label"]
        volume_channel_annotations.append(
            {
                "channel_id": str(channel_id),
                "color": hex_to_rgba_normalized(channel["color"]),
                "label": label,
            }
        )

    return volume_channel_annotations


def get_ome_tiff_origins(boxes_dict: dict, downsamplings: list[DownsamplingLevelInfo]):
    # NOTE: origins seem to be 0, 0, 0, as they are not specified
    available = list(filter(lambda a: a["available"] == True, downsamplings))
    downsampling_levels = sorted([a["level"] for a in available])
    for level in downsampling_levels:
        downsampling_level = str(level)
        boxes_dict[downsampling_level]["origin"] = [0, 0, 0]
