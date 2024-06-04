from cellstar_db.models import (
    DetailLvlsMetadata,
    MeshComponentNumbers,
    MeshesMetadata,
    MeshListMetadata,
    MeshMetadata,
    MeshSegmentationSetsMetadata,
    Metadata,
    SamplingInfo,
    SegmentationLatticesMetadata,
    TimeInfo,
)
from cellstar_preprocessor.flows.common import (
    get_downsamplings,
    open_zarr_structure_from_path,
)
from cellstar_preprocessor.flows.constants import (
    LATTICE_SEGMENTATION_DATA_GROUPNAME,
    MESH_SEGMENTATION_DATA_GROUPNAME,
)
from cellstar_preprocessor.model.input import SegmentationPrimaryDescriptor
from cellstar_preprocessor.model.segmentation import InternalSegmentation


def _get_segmentation_sampling_info(
    root_data_group, sampling_info_dict, volume_sampling_info_dict
):
    for res_gr_name, res_gr in root_data_group.groups():
        # create layers (time gr, channel gr)
        sampling_info_dict["boxes"][res_gr_name] = {
            "origin": volume_sampling_info_dict["boxes"][res_gr_name]["origin"],
            "voxel_size": volume_sampling_info_dict["boxes"][res_gr_name]["voxel_size"],
            "grid_dimensions": None,
            # 'force_dtype': None
        }

        for time_gr_name, time_gr in res_gr.groups():
            sampling_info_dict["boxes"][res_gr_name][
                "grid_dimensions"
            ] = time_gr.grid.shape


def extract_metadata_from_sff_segmentation(internal_segmentation: InternalSegmentation):
    # PLAN:
    # takes prefilled metadata dict from map metadata
    # takes internal segmentation
    # checks primary descriptor
    root = open_zarr_structure_from_path(
        internal_segmentation.intermediate_zarr_structure_path
    )
    metadata_dict: Metadata = root.attrs["metadata_dict"]

    if (
        internal_segmentation.primary_descriptor
        == SegmentationPrimaryDescriptor.three_d_volume
    ):
        time_info_for_all_lattices: TimeInfo = {
            "end": 0,
            "kind": "range",
            "start": 0,
            "units": "millisecond",
        }

        lattice_ids = []
        source_axes_units = {}

        segmentation_lattices_metadata: SegmentationLatticesMetadata = metadata_dict[
            "segmentation_lattices"
        ]

        for lattice_id, lattice_gr in root[
            LATTICE_SEGMENTATION_DATA_GROUPNAME
        ].groups():
            downsamplings = get_downsamplings(data_group=lattice_gr)
            lattice_ids.append(lattice_id)

            sampling_info: SamplingInfo = {
                "spatial_downsampling_levels": downsamplings,
                "boxes": {},
                "time_transformations": [],
                "source_axes_units": source_axes_units,
                # TODO: original axes order?
                "original_axis_order": [0, 1, 2],
            }
            segmentation_lattices_metadata["segmentation_sampling_info"][
                str(lattice_id)
            ] = sampling_info
            segmentation_lattices_metadata["time_info"][
                str(lattice_id)
            ] = time_info_for_all_lattices

            _get_segmentation_sampling_info(
                root_data_group=lattice_gr,
                sampling_info_dict=segmentation_lattices_metadata[
                    "segmentation_sampling_info"
                ][str(lattice_id)],
                volume_sampling_info_dict=metadata_dict["volumes"][
                    "volume_sampling_info"
                ],
            )

        segmentation_lattices_metadata["segmentation_ids"] = lattice_ids
        metadata_dict["segmentation_lattices"] = segmentation_lattices_metadata

    elif (
        internal_segmentation.primary_descriptor
        == SegmentationPrimaryDescriptor.mesh_list
    ):
        mesh_segmentation_sets_metadata: MeshSegmentationSetsMetadata = metadata_dict[
            "segmentation_meshes"
        ]

        time_info_for_all_mesh_sets: TimeInfo = {
            "end": 0,
            "kind": "range",
            "start": 0,
            "units": "millisecond",
        }
        # order: segment_ids, detail_lvls, time, channel, mesh_ids
        for set_id, set_gr in root[MESH_SEGMENTATION_DATA_GROUPNAME].groups():
            # NOTE: mesh has no time
            mesh_segmentation_sets_metadata["time_info"][
                str(set_id)
            ] = time_info_for_all_mesh_sets
            mesh_segmentation_sets_metadata["segmentation_ids"].append(set_id)
            mesh_set_metadata: MeshesMetadata = {
                "detail_lvl_to_fraction": internal_segmentation.simplification_curve,
                "mesh_timeframes": {},
            }
            for timeframe_index, timeframe_gr in set_gr.groups():
                mesh_comp_num: MeshComponentNumbers = {"segment_ids": {}}
                for segment_id, segment in timeframe_gr.groups():
                    detail_lvls_metadata: DetailLvlsMetadata = {"detail_lvls": {}}
                    for detail_lvl, detail_lvl_gr in segment.groups():
                        mesh_list_metadata: MeshListMetadata = {"mesh_ids": {}}
                        for mesh_id, mesh in detail_lvl_gr.groups():
                            mesh_metadata: MeshMetadata = {}
                            for mesh_component_name, mesh_component in mesh.arrays():
                                mesh_metadata[f"num_{mesh_component_name}"] = (
                                    mesh_component.attrs[f"num_{mesh_component_name}"]
                                )
                            mesh_list_metadata["mesh_ids"][int(mesh_id)] = mesh_metadata
                        detail_lvls_metadata["detail_lvls"][
                            int(detail_lvl)
                        ] = mesh_list_metadata
                    mesh_comp_num["segment_ids"][int(segment_id)] = detail_lvls_metadata
                mesh_set_metadata["mesh_timeframes"][
                    int(timeframe_index)
                ] = mesh_comp_num
            mesh_segmentation_sets_metadata["segmentation_metadata"][
                set_id
            ] = mesh_set_metadata
        metadata_dict["segmentation_meshes"] = mesh_segmentation_sets_metadata

        #     mesh_comp_num["segment_ids"][segment_id] = {"detail_lvls": {}}
        #     for detail_lvl, detail_lvl_gr in segment.groups():
        #         mesh_comp_num["segment_ids"][segment_id]["detail_lvls"][detail_lvl] = {
        #             "mesh_ids": {}
        #         }
        #         # NOTE: mesh has no time and channel (both equal zero)
        #         for mesh_id, mesh in detail_lvl_gr["0"]["0"].groups():
        #             mesh_comp_num["segment_ids"][segment_id]["detail_lvls"][detail_lvl][
        #                 "mesh_ids"
        #             ][mesh_id] = {}
        #             for mesh_component_name, mesh_component in mesh.arrays():
        #                 d_ref = mesh_comp_num["segment_ids"][segment_id]["detail_lvls"][
        #                     detail_lvl
        #                 ]["mesh_ids"][mesh_id]
        #                 d_ref[f"num_{mesh_component_name}"] = mesh_component.attrs[
        #                     f"num_{mesh_component_name}"
        #                 ]

        # detail_lvl_to_fraction_dict = internal_segmentation.simplification_curve

        # metadata_dict["segmentation_meshes"]["mesh_component_numbers"] = mesh_comp_num
        # metadata_dict["segmentation_meshes"][
        #     "detail_lvl_to_fraction"
        # ] = detail_lvl_to_fraction_dict

    root.attrs["metadata_dict"] = metadata_dict
    return metadata_dict
