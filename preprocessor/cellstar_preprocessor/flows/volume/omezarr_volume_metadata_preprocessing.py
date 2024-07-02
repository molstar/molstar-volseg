from cellstar_preprocessor.flows.zarr_methods import open_zarr
from cellstar_preprocessor.flows.zarr_methods import get_downsamplings
import numpy as np
import zarr
from cellstar_db.file_system.constants import VOLUME_DATA_GROUPNAME
from cellstar_db.models import (
    DownsamplingLevelInfo,
    EntryId,
    Metadata,
    TimeInfo,
    VolumeSamplingInfo,
    VolumesMetadata,
)
from cellstar_preprocessor.flows.common import (
    convert_to_angstroms,
)
from cellstar_preprocessor.flows.constants import LATTICE_SEGMENTATION_DATA_GROUPNAME
from cellstar_preprocessor.model.volume import InternalVolume


def _get_first_available_resolution(downsamplings: list[DownsamplingLevelInfo]):
    available = list(filter(lambda a: a["available"] == True, downsamplings))
    downsampling_levels = sorted([a["level"] for a in available])
    first_available_resolution = downsampling_levels[0]
    return first_available_resolution


def _get_axis_order_omezarr(ome_zarr_attrs):
    # TODO: fix this for the case with CYX axes
    axes_names_to_numbers = {"z": 2, "y": 1, "x": 0}
    axes_order = []
    multiscales = ome_zarr_attrs["multiscales"]
    # NOTE: can be multiple multiscales, here picking just 1st
    axes = multiscales[0]["axes"]
    for axis in axes[-3:]:
        axes_order.append(axes_names_to_numbers[axis["name"]])

    return axes_order


def get_origins(ome_zarr_attrs, boxes_dict: dict):
    multiscales = ome_zarr_attrs["multiscales"]
    # NOTE: can be multiple multiscales, here picking just 1st
    axes = multiscales[0]["axes"]
    datasets_meta = multiscales[0]["datasets"]
    for index, level in enumerate(datasets_meta):
        # check index is not in boxes dict for the case of removing original res
        if level["path"] not in boxes_dict:
            continue
        if (
            # NOTE: checks if there is translation in the list, since if present it is always 2nd
            len(level["coordinateTransformations"]) == 2
            and level["coordinateTransformations"][1]["type"] == "translation"
        ):
            # NOTE: why there is [1] not [0]? Because translation should be second
            translation_arr = level["coordinateTransformations"][1]["translation"]

            # instead of swapaxes, -1, -2, -3
            boxes_dict[level["path"]].origin = [
                translation_arr[-1],
                translation_arr[-2],
                translation_arr[-3],
            ]
        else:
            boxes_dict[level["path"]].origin = [0, 0, 0]

    # apply global

    if "coordinateTransformations" in multiscales[0]:
        if multiscales[0]["coordinateTransformations"][1]["type"] == "translation":
            global_translation_arr = multiscales[0]["coordinateTransformations"][1][
                "translation"
            ]
            global_translation_arr = global_translation_arr[-3:]
            global_translation_arr[0], global_translation_arr[2] = (
                global_translation_arr[2],
                global_translation_arr[0],
            )

            for resolution in boxes_dict:
                boxes_dict[resolution].origin = [
                    a + b
                    for a, b in zip(
                        boxes_dict[resolution].origin, global_translation_arr
                    )
                ]

    # convert to angstroms
    for resolution in boxes_dict:
        boxes_dict[resolution].origin[0] = convert_to_angstroms(
            boxes_dict[resolution].origin[0], input_unit=axes[-1]["unit"]
        )
        boxes_dict[resolution].origin[1] = convert_to_angstroms(
            boxes_dict[resolution].origin[1], input_unit=axes[-2]["unit"]
        )
        boxes_dict[resolution].origin[2] = convert_to_angstroms(
            boxes_dict[resolution].origin[2], input_unit=axes[-3]["unit"]
        )

    return boxes_dict


def get_voxel_sizes_in_downsamplings(ome_zarr_attrs, boxes_dict):
    multiscales = ome_zarr_attrs["multiscales"]
    datasets_meta = multiscales[0]["datasets"]
    axes = multiscales[0]["axes"]

    for index, level in enumerate(datasets_meta):
        # check index is not in boxes dict for the case of removing original res
        if level["path"] not in boxes_dict:
            continue

        scale_arr = level["coordinateTransformations"][0]["scale"]
        if len(scale_arr) == 5:
            scale_arr = scale_arr[2:]
        elif len(scale_arr) == 4:
            scale_arr = scale_arr[1:]
        else:
            raise Exception("Length of scale arr is not supported")

        # x and z swapped
        boxes_dict[level["path"]].voxel_size = [
            convert_to_angstroms(scale_arr[2], input_unit=axes[-1]["unit"]),
            convert_to_angstroms(scale_arr[1], input_unit=axes[-2]["unit"]),
            convert_to_angstroms(scale_arr[0], input_unit=axes[-3]["unit"]),
        ]

        if "coordinateTransformations" in multiscales[0]:
            if multiscales[0]["coordinateTransformations"][0]["type"] == "scale":
                global_scale_arr = multiscales[0]["coordinateTransformations"][0][
                    "scale"
                ]
                if len(global_scale_arr) == 5:
                    global_scale_arr = global_scale_arr[2:]
                elif len(global_scale_arr) == 4:
                    global_scale_arr = global_scale_arr[1:]
                else:
                    raise Exception("Length of scale arr is not supported")
                boxes_dict[level["path"]].voxel_size[0] = (
                    boxes_dict[level["path"]].voxel_size[0] * global_scale_arr[2]
                )
                boxes_dict[level["path"]].voxel_size[1] = (
                    boxes_dict[level["path"]].voxel_size[1] * global_scale_arr[1]
                )
                boxes_dict[level["path"]].voxel_size[2] = (
                    boxes_dict[level["path"]].voxel_size[2] * global_scale_arr[0]
                )
            else:
                raise Exception("First transformation should be of scale type")

    return boxes_dict

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

                arr_view = channel_arr[...]
                # if QUANTIZATION_DATA_DICT_ATTR_NAME in arr.attrs:
                #     data_dict = arr.attrs[QUANTIZATION_DATA_DICT_ATTR_NAME]
                #     data_dict['data'] = arr_view
                #     arr_view = decode_quantized_data(data_dict)
                #     if isinstance(arr_view, da.Array):
                #         arr_view = arr_view.compute()

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


def _get_segmentation_sampling_info(root_data_group, sampling_info_dict):
    for res_gr_name, res_gr in root_data_group.groups():
        # create layers (time gr, channel gr)
        sampling_info_dict.boxes[res_gr_name] = {
            "origin": None,
            "voxel_size": None,
            "grid_dimensions": None,
            # 'force_dtype': None
        }

        for time_gr_name, time_gr in res_gr.groups():
            sampling_info_dict.boxes[res_gr_name][
                "grid_dimensions"
            ] = time_gr.grid.shape


def _get_source_axes_units(ome_zarr_root_attrs: zarr.Group):
    d = {}
    multiscales = ome_zarr_root_attrs["multiscales"]
    # NOTE: can be multiple multiscales, here picking just 1st
    axes = multiscales[0]["axes"]
    for axis in axes:
        if not "unit" in axis or axis["type"] == "channel":
            d[axis["name"]] = None
        else:
            d[axis["name"]] = axis["unit"]

    return d


def omezarr_volume_metadata_preprocessing(v: InternalVolume):
    root = open_zarr(
        v.path
    )
    ome_zarr_root = open_zarr(v.input_path)
    w = v.get_omezarr_wrapper()
    
    # TODO: refactor
    w.add_defaults_to_ome_zarr_attrs()

    volume_downsamplings = get_downsamplings(data_group=root[VOLUME_DATA_GROUPNAME])
    
    channel_ids = v.get_channel_ids()
    start_time, end_time = v.get_start_end_time(v.get_volume_data_group())

    m = v.get_metadata()    
    v.set_entry_id_in_metadata()
    
    m.volumes = VolumesMetadata(
        channel_ids=channel_ids,
        time_info=TimeInfo(
            kind="range",
            start=start_time,
            end=end_time,
            # omezarr wrapper
            units=w.get_time_units(),
        ),
        sampling_info=VolumeSamplingInfo(
            spatial_downsampling_levels=volume_downsamplings,
            boxes={},
            descriptive_statistics={},
            time_transformations=[],
            source_axes_units=v.get_source_axes_units(),
            original_axis_order=v.get_original_axis_order(),
        ),
    )

    time_transformations = w.process_time_transformations()
    v.set_time_transformations(time_transformations)
    
    
    sampling_info = v.get_volume_sampling_info()
    m.volumes.sampling_info = sampling_info
    
    v.get_volume_sampling_info()
    v.set_metadata(m)
    return m
