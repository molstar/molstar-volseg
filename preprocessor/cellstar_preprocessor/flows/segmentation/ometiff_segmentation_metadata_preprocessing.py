import dask.array as da
import zarr
from cellstar_db.models import OMETIFFSpecificExtraData
from cellstar_preprocessor.flows.common import (
    _get_ome_tiff_voxel_sizes_in_downsamplings,
    get_downsamplings,
    get_ome_tiff_origins,
    open_zarr_structure_from_path,
)
from cellstar_preprocessor.flows.constants import LATTICE_SEGMENTATION_DATA_GROUPNAME
from cellstar_preprocessor.model.segmentation import InternalSegmentation

# SHORT_UNIT_NAMES_TO_LONG = {
#     'µm': 'micrometer',
#     # TODO: support other units
# }


def _get_source_axes_units():
    # NOTE: hardcoding this for now
    spatial_units = "micrometer"
    d = {"x": spatial_units, "y": spatial_units, "z": spatial_units}
    # d = {}
    return d


# def _convert_short_units_to_long(short_unit_name: str):
#     # TODO: support conversion of other axes units (currently only µm to micrometer).
#     # https://www.openmicroscopy.org/Schemas/Documentation/Generated/OME-2016-06/ome_xsd.html#Pixels_PhysicalSizeXUnit
#     if short_unit_name in SHORT_UNIT_NAMES_TO_LONG:
#         return SHORT_UNIT_NAMES_TO_LONG[short_unit_name]
#     else:
#         raise Exception('Short unit name is not supported')

# def _get_ometiff_physical_size(ome_tiff_metadata):
#     d = {}
#     if 'PhysicalSizeX' in ome_tiff_metadata:
#         d['x'] = ome_tiff_metadata['PhysicalSizeX']
#     else:
#         d['x'] = 1.0

#     if 'PhysicalSizeY' in ome_tiff_metadata:
#         d['y'] = ome_tiff_metadata['PhysicalSizeY']
#     else:
#         d['y'] = 1.0

#     if 'PhysicalSizeZ' in ome_tiff_metadata:
#         d['z'] = ome_tiff_metadata['PhysicalSizeZ']
#     else:
#         d['z'] = 1.0

#     return d


def _get_segmentation_sampling_info(root_data_group, sampling_info_dict):
    for res_gr_name, res_gr in root_data_group.groups():
        # create layers (time gr, channel gr)
        sampling_info_dict["boxes"][res_gr_name] = {
            "origin": None,
            "voxel_size": None,
            "grid_dimensions": None,
            # 'force_dtype': None
        }

        for time_gr_name, time_gr in res_gr.groups():
            sampling_info_dict["boxes"][res_gr_name][
                "grid_dimensions"
            ] = time_gr.grid.shape


# def _get_ometiff_axes_units(ome_tiff_metadata):
#     axes_units = {}
#     if 'PhysicalSizeXUnit' in ome_tiff_metadata:
#         axes_units['x'] = _convert_short_units_to_long(ome_tiff_metadata['PhysicalSizeXUnit'])
#     else:
#         axes_units['x'] = 'micrometer'

#     if 'PhysicalSizeYUnit' in ome_tiff_metadata:
#         axes_units['y'] = _convert_short_units_to_long(ome_tiff_metadata['PhysicalSizeYUnit'])
#     else:
#         axes_units['y'] = 'micrometer'

#     if 'PhysicalSizeZUnit' in ome_tiff_metadata:
#         axes_units['z'] = _convert_short_units_to_long(ome_tiff_metadata['PhysicalSizeZUnit'])
#     else:
#         axes_units['z'] = 'micrometer'

#     return axes_units


# def _get_ome_tiff_voxel_sizes_in_downsamplings(boxes_dict, downsamplings, ometiff_metadata):
#     # original voxel size - in XML metadata (PhysicalSizeX,Y,Z)
#     # downsampling voxel size - constructed based on how many downsamplings there are
#     # plan:
#     # 1. for 0th downsampling - get from metadata
#     # 2. TODO: for other levels - iterate over volume_downsamplings
#     # axis order? XYZ? we change it to XYZ when processing volume

#     # ometiff_axes_units_dict = _get_ometiff_axes_units(ometiff_metadata)
#     # ometiff_physical_size_dict = _get_ometiff_physical_size(ometiff_metadata)

#     for level in downsamplings:
#         downsampling_level = str(level)
#         if downsampling_level == '1':
#             boxes_dict[downsampling_level]['voxel_size'] = [
#                 _convert_to_angstroms(ometiff_physical_size_dict['x'], ometiff_axes_units_dict['x']),
#                 _convert_to_angstroms(ometiff_physical_size_dict['y'], ometiff_axes_units_dict['y']),
#                 _convert_to_angstroms(ometiff_physical_size_dict['z'], ometiff_axes_units_dict['z'])
#             ]
#         else:
#             # NOTE: rounding error - if one of dimensions in original data is odd
#             boxes_dict[downsampling_level]['voxel_size'] = [
#                 _convert_to_angstroms(ometiff_physical_size_dict['x'] * int(downsampling_level), ometiff_axes_units_dict['x']),
#                 _convert_to_angstroms(ometiff_physical_size_dict['y'] * int(downsampling_level), ometiff_axes_units_dict['y']),
#                 _convert_to_angstroms(ometiff_physical_size_dict['z'] * int(downsampling_level), ometiff_axes_units_dict['z'])
#             ]


def _get_allencell_voxel_size(root: zarr.Group) -> list[float, float, float]:
    return root.attrs["extra_data"]["scale_micron"]


def _get_volume_sampling_info(root_data_group: zarr.Group, sampling_info_dict):
    for res_gr_name, res_gr in root_data_group.groups():
        # create layers (time gr, channel gr)
        sampling_info_dict["boxes"][res_gr_name] = {
            "origin": None,
            "voxel_size": None,
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


def ometiff_segmentation_metadata_preprocessing(internal_segmentation: InternalSegmentation):
    root = open_zarr_structure_from_path(
        internal_segmentation.intermediate_zarr_structure_path
    )
    # TODO: same as with volume metadata
    metadata_dict = root.attrs["metadata_dict"]
    ometiff_custom_data: OMETIFFSpecificExtraData = internal_segmentation.custom_data[
        "dataset_specific_data"
    ]["ometiff"]
    ometiff_metadata = ometiff_custom_data["ometiff_source_metadata"]

    # ometiff_metadata = internal_segmentation.custom_data['ometiff_metadata']
    # NOTE: sample ometiff has no time
    # channel_ids = _get_allencell_segmentation_channel_ids(root)
    start_time = 0
    end_time = ometiff_metadata["SizeT"] - 1
    time_units = "millisecond"

    # original_voxel_size_in_micrometers = _get_allencell_voxel_size(root)

    if LATTICE_SEGMENTATION_DATA_GROUPNAME in root:
        lattice_ids = []

        metadata_dict["segmentation_lattices"] = {
            "segmentation_ids": [],
            "segmentation_sampling_info": {},
            "time_info": {},
        }
        for label_gr_name, label_gr in root[
            LATTICE_SEGMENTATION_DATA_GROUPNAME
        ].groups():
            # each label group is lattice id
            lattice_id = label_gr_name

            # segm_downsamplings = sorted(label_gr.group_keys())
            # # convert to ints
            # segm_downsamplings = sorted([int(x) for x in segm_downsamplings])
            # lattice_dict[str(lattice_id)] = segm_downsamplings

            lattice_ids.append(lattice_id)

            segmentation_downsamplings = get_downsamplings(data_group=label_gr)

            metadata_dict["segmentation_lattices"]["segmentation_sampling_info"][
                str(lattice_id)
            ] = {
                # Info about "downsampling dimension"
                "spatial_downsampling_levels": segmentation_downsamplings,
                # the only thing with changes with SPATIAL downsampling is box!
                "boxes": {},
                "time_transformations": [],
                "source_axes_units": _get_source_axes_units(),
                "original_axis_order": (0, 1, 2),
            }

            _get_segmentation_sampling_info(
                root_data_group=label_gr,
                sampling_info_dict=metadata_dict["segmentation_lattices"][
                    "segmentation_sampling_info"
                ][str(lattice_id)],
            )

            get_ome_tiff_origins(
                boxes_dict=metadata_dict["segmentation_lattices"][
                    "segmentation_sampling_info"
                ][str(lattice_id)]["boxes"],
                downsamplings=segmentation_downsamplings,
            )

            _get_ome_tiff_voxel_sizes_in_downsamplings(
                internal_volume_or_segmentation=internal_segmentation,
                boxes_dict=metadata_dict["segmentation_lattices"][
                    "segmentation_sampling_info"
                ][str(lattice_id)]["boxes"],
                downsamplings=segmentation_downsamplings,
                ometiff_metadata=ometiff_metadata,
            )

            # NOTE: for now time 0
            metadata_dict["segmentation_lattices"]["time_info"][label_gr_name] = {
                "kind": "range",
                "start": start_time,
                "end": end_time,
                "units": time_units,
            }

        metadata_dict["segmentation_lattices"]["segmentation_ids"] = lattice_ids

    root.attrs["metadata_dict"] = metadata_dict
    return metadata_dict
