from cellstar_preprocessor.flows.common import (
    get_downsamplings,
    open_zarr_structure_from_path,
)
from cellstar_preprocessor.flows.constants import LATTICE_SEGMENTATION_DATA_GROUPNAME
from cellstar_preprocessor.model.segmentation import InternalSegmentation


def _get_segmentation_sampling_info(
    root_data_group, sampling_info_dict, volume_sampling_info_dict
):
    for res_gr_name, res_gr in root_data_group.groups():
        # create layers (time gr, channel gr)
        sampling_info_dict["boxes"][res_gr_name] = {
            "origin": volume_sampling_info_dict["boxes"][res_gr_name]["origin"],
            # TODO: voxel size needs to be taken from header of nii file for segmentation?
            "voxel_size": volume_sampling_info_dict["boxes"][res_gr_name]["voxel_size"],
            "grid_dimensions": None,
            # 'force_dtype': None
        }

        for time_gr_name, time_gr in res_gr.groups():
            first_group_key = sorted(time_gr.group_keys())[0]

            sampling_info_dict["boxes"][res_gr_name]["grid_dimensions"] = time_gr[
                first_group_key
            ].grid.shape

            for channel_gr_name, channel_gr in time_gr.groups():
                assert (
                    sampling_info_dict["boxes"][res_gr_name]["grid_dimensions"]
                    == channel_gr.grid.shape
                )


def nii_segmentation_metadata_preprocessing(
    internal_segmentation: InternalSegmentation,
):
    # PLAN:
    # takes prefilled metadata dict from nii metadata
    # takes internal segmentation
    root = open_zarr_structure_from_path(
        internal_segmentation.intermediate_zarr_structure_path
    )
    metadata_dict = root.attrs["metadata_dict"]

    # nii has one channel
    channel_ids = [0]
    start_time = 0
    end_time = 0
    time_units = "millisecond"
    lattice_ids = []

    # TODO: check - some units are defined (spatial?)
    source_axes_units = {}

    for lattice_id, lattice_gr in root[LATTICE_SEGMENTATION_DATA_GROUPNAME].groups():
        downsamplings = get_downsamplings(data_group=lattice_gr)
        lattice_ids.append(lattice_id)

        metadata_dict["segmentation_lattices"]["segmentation_sampling_info"][
            str(lattice_id)
        ] = {
            # Info about "downsampling dimension"
            "spatial_downsampling_levels": downsamplings,
            # the only thing with changes with SPATIAL downsampling is box!
            "boxes": {},
            "time_transformations": [],
            "source_axes_units": source_axes_units,
        }
        _get_segmentation_sampling_info(
            root_data_group=lattice_gr,
            sampling_info_dict=metadata_dict["segmentation_lattices"][
                "segmentation_sampling_info"
            ][str(lattice_id)],
            volume_sampling_info_dict=metadata_dict["volumes"]["volume_sampling_info"],
        )

        metadata_dict["segmentation_lattices"]["channel_ids"][lattice_id] = channel_ids

        metadata_dict["segmentation_lattices"]["time_info"][lattice_id] = {
            "kind": "range",
            "start": start_time,
            "end": end_time,
            "units": time_units,
        }

    metadata_dict["segmentation_lattices"]["segmentation_ids"] = lattice_ids

    root.attrs["metadata_dict"] = metadata_dict
    return metadata_dict
