import numpy as np
import zarr
from cellstar_db.models import DownsamplingLevelInfo, convert_to_angstroms
from cellstar_preprocessor.flows.zarr_methods import open_zarr
from cellstar_preprocessor.model.segmentation import InternalSegmentation


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


def get_time_transformations(ome_zarr_attrs, time_transformations_list: list):
    multiscales = ome_zarr_attrs["multiscales"]
    # NOTE: can be multiple multiscales, here picking just 1st
    axes = multiscales[0]["axes"]
    datasets_meta = multiscales[0]["datasets"]
    if axes[0]["name"] == "t":
        for index, level in enumerate(datasets_meta):
            scale_arr = level["coordinateTransformations"][0]["scale"]
            if len(scale_arr) == 5:
                factor = scale_arr[0]
                if "coordinateTransformations" in multiscales[0]:
                    if (
                        multiscales[0]["coordinateTransformations"][0]["type"]
                        == "scale"
                    ):
                        factor = (
                            factor
                            * multiscales[0]["coordinateTransformations"][0]["scale"][0]
                        )
                time_transformations_list.append(
                    {"downsampling_level": level["path"], "factor": factor}
                )
            else:
                raise Exception("Length of scale arr is not supported")
        return time_transformations_list
    else:
        return time_transformations_list


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


def get_time_units(ome_zarr_attrs):
    # NOTE: default is milliseconds if time axes is not present
    multiscales = ome_zarr_attrs["multiscales"]
    # NOTE: can be multiple multiscales, here picking just 1st
    axes = multiscales[0]["axes"]
    if axes[0]["name"] == "t":
        # NOTE: may not have it, then we default to ms
        if "unit" in axes[0]:
            return axes[0]["unit"]
        else:
            return "millisecond"
    else:
        return "millisecond"


def _get_channel_ids(time_data_group, segmentation_data=False) -> list:
    if segmentation_data:
        channel_ids = sorted(time_data_group.group_keys())
    else:
        channel_ids = sorted(time_data_group.array_keys())
    channel_ids = sorted(str(x) for x in channel_ids)

    return channel_ids


def _get_start_end_time(resolution_data_group) -> tuple[int, int]:
    time_intervals = sorted(resolution_data_group.group_keys())
    time_intervals = sorted(int(x) for x in time_intervals)
    start_time = min(time_intervals)
    end_time = max(time_intervals)
    return (start_time, end_time)


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


def _add_defaults_to_ome_zarr_attrs(ome_zarr_root: zarr.Group):
    # TODO: try put/update
    # 1. add units to axes
    # NOTE: can be multiple multiscales, here picking just 1st
    d = ome_zarr_root.attrs.asdict()
    for axis in d["multiscales"][0]["axes"]:
        if not "unit" in axis:
            if axis["type"] == "space":
                axis["unit"] = "angstrom"
            if axis["type"] == "time":
                axis["unit"] = "millisecond"

    return d


def omezarr_segmentation_metadata_preprocessing(s: InternalSegmentation):
    root = open_zarr(s.path)
    s.set_segmentation_lattices_metadata()

    # m: Metadata = root.attrs["metadata_dict"]
    # lattice_ids = []
    # assert LATTICE_SEGMENTATION_DATA_GROUPNAME, "No segmentation data available"
    # m.segmentation_lattices = {
    #     "segmentation_ids": [],
    #     "segmentation_sampling_info": {},
    #     "time_info": {},
    # }
    # for label_gr_name, label_gr in root[LATTICE_SEGMENTATION_DATA_GROUPNAME].groups():
    #     new_segm_attrs_dict = _add_defaults_to_ome_zarr_attrs(
    #         ome_zarr_root=ome_zarr_root.labels[label_gr_name]
    #     )
    #     ome_zarr_root.labels[label_gr_name].attrs.put(new_segm_attrs_dict)

    #     # each label group is lattice id
    #     lattice_id = label_gr_name

    #     # segm_downsamplings = sorted(label_gr.group_keys())
    #     # # convert to ints
    #     # segm_downsamplings = sorted([int(x) for x in segm_downsamplings])
    #     # lattice_dict[str(lattice_id)] = segm_downsamplings

    #     lattice_ids.append(lattice_id)

    #     segmentation_downsamplings = get_downsamplings(data_group=label_gr)

    #     first_available_segm_resolution = _get_first_available_resolution(
    #         segmentation_downsamplings
    #     )
    #     m.segmentation_lattices["segmentation_sampling_info"][
    #         str(lattice_id)
    #     ] = {
    #         # Info about "downsampling dimension"
    #         "spatial_downsampling_levels": segmentation_downsamplings,
    #         # the only thing with changes with SPATIAL downsampling is box!
    #         "boxes": {},
    #         "time_transformations": [],
    #         "source_axes_units": _get_source_axes_units(
    #             ome_zarr_root_attrs=ome_zarr_root.labels[str(label_gr_name)].attrs
    #         ),
    #         "original_axis_order": _get_axis_order_omezarr(
    #             ome_zarr_attrs=ome_zarr_root.labels[str(label_gr_name)].attrs
    #         ),
    #     }
    #     get_time_transformations(
    #         ome_zarr_attrs=ome_zarr_root.labels[str(label_gr_name)].attrs,
    #         time_transformations_list=m.segmentation_lattices[
    #             "segmentation_sampling_info"
    #         ][str(lattice_id)]["time_transformations"],
    #     )
    #     _get_segmentation_sampling_info(
    #         root_data_group=label_gr,
    #         sampling_info_dict=m.segmentation_lattices[
    #             "segmentation_sampling_info"
    #         ][str(lattice_id)],
    #     )

    #     get_origins(
    #         ome_zarr_attrs=ome_zarr_root.labels[str(label_gr_name)].attrs,
    #         boxes_dict=m.segmentation_lattices[
    #             "segmentation_sampling_info"
    #         ][str(lattice_id)].boxes,
    #     )
    #     get_voxel_sizes_in_downsamplings(
    #         ome_zarr_attrs=ome_zarr_root.labels[str(label_gr_name)].attrs,
    #         boxes_dict=m.segmentation_lattices[
    #             "segmentation_sampling_info"
    #         ][str(lattice_id)].boxes,
    #     )

    #     segm_start_time, segm_end_time = _get_start_end_time(
    #         resolution_data_group=label_gr[first_available_segm_resolution]
    #     )
    #     # metadata_dict.segmentation_lattices["time_info"][label_gr_name] = {
    #     #     kind="range",
    #     #     start=segm_start_time,
    #     #     end=segm_end_time,
    #     #     units=get_time_units(
    #     #         ome_zarr_attrs=ome_zarr_root.labels[str(label_gr_name)].attrs
    #     #     ),
    #     # }

    # m.segmentation_lattices.ids = lattice_ids

    # root.attrs["metadata_dict"] = m
    # return m
