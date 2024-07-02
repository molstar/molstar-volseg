import zarr
from cellstar_db.models import SegmentationPrimaryDescriptor
from cellstar_preprocessor.flows.constants import (
    LATTICE_SEGMENTATION_DATA_GROUPNAME,
    MESH_SEGMENTATION_DATA_GROUPNAME,
    MESH_SIMPLIFICATION_LEVELS_PER_ORDER,
    MESH_SIMPLIFICATION_N_LEVELS,
)
from cellstar_preprocessor.flows.segmentation.helper_methods import (
    extract_raw_annotations_from_sff,
    hdf5_to_zarr,
    lattice_data_to_np_arr,
    make_simplification_curve,
    map_value_to_segment_id,
    store_segmentation_data_in_zarr_structure,
    write_mesh_component_data_to_zarr_arr,
)
from cellstar_preprocessor.flows.zarr_methods import open_zarr
from cellstar_preprocessor.model.segmentation import InternalSegmentation
from vedo import Mesh


def sff_segmentation_preprocessing(internal_segmentation: InternalSegmentation):
    hdf5_to_zarr(internal_segmentation=internal_segmentation)

    zarr_structure: zarr.Group = open_zarr(internal_segmentation.path)

    internal_segmentation.raw_sff_annotations = extract_raw_annotations_from_sff(
        segm_file_path=internal_segmentation.input_path
    )

    # PLAN:
    # 1. Convert hff to intermediate zarr structure
    # 2. Process it with one of 2 methods (3d volume segmentation, mesh segmentation)
    if zarr_structure.primary_descriptor[0] == b"three_d_volume":
        segm_data_gr: zarr.Group = zarr_structure.create_group(
            LATTICE_SEGMENTATION_DATA_GROUPNAME
        )
        internal_segmentation.primary_descriptor = (
            SegmentationPrimaryDescriptor.three_d_volume
        )
        internal_segmentation.value_to_segment_id_dict = map_value_to_segment_id(
            zarr_structure
        )
        _process_three_d_volume_segmentation_data(
            segm_data_gr, zarr_structure, internal_segmentation=internal_segmentation
        )
    elif zarr_structure.primary_descriptor[0] == b"mesh_list":
        segm_data_gr: zarr.Group = zarr_structure.create_group(
            MESH_SEGMENTATION_DATA_GROUPNAME
        )
        internal_segmentation.primary_descriptor = (
            SegmentationPrimaryDescriptor.mesh_list
        )
        internal_segmentation.simplification_curve = make_simplification_curve(
            MESH_SIMPLIFICATION_N_LEVELS, MESH_SIMPLIFICATION_LEVELS_PER_ORDER
        )

        # NOTE: single mesh set group and timeframe group
        mesh_set_gr = segm_data_gr.create_group("0")
        timeframe_gr = mesh_set_gr.create_group(0)

        _process_mesh_segmentation_data(
            timeframe_gr, zarr_structure, internal_segmentation=internal_segmentation
        )

    print("Segmentation processed")


def _process_three_d_volume_segmentation_data(
    segm_data_gr: zarr.Group,
    zarr_structure: zarr.Group,
    internal_segmentation: InternalSegmentation,
):
    for gr_name, gr in zarr_structure.lattice_list.groups():
        # gr is a 'lattice' obj in lattice list
        lattice_id = str(gr.id[...])
        segm_arr = lattice_data_to_np_arr(
            data=gr.data[0],
            mode=gr.mode[0],
            endianness=gr.endianness[0],
            arr_shape=(gr.size.cols[...], gr.size.rows[...], gr.size.sections[...]),
        )

        lattice_gr = segm_data_gr.create_group(gr_name)
        value_to_segment_id_dict = internal_segmentation.value_to_segment_id_dict
        params_for_storing = internal_segmentation.params_for_storing

        store_segmentation_data_in_zarr_structure(
            original_data=segm_arr,
            lattice_data_group=lattice_gr,
            value_to_segment_id_dict_for_specific_lattice_id=value_to_segment_id_dict[
                lattice_id
            ],
            params_for_storing=params_for_storing,
        )


def _process_mesh_segmentation_data(
    timeframe_gr: zarr.Group,
    zarr_structure: zarr.Group,
    internal_segmentation: InternalSegmentation,
):
    params_for_storing = internal_segmentation.params_for_storing

    for segment_name, segment in zarr_structure.segment_list.groups():
        segment_id = int(segment.id[...])
        single_segment_group = timeframe_gr.create_group(segment_id)
        single_detail_lvl_group = single_segment_group.create_group(1)
        if "mesh_list" in segment:
            for mesh_name, mesh in segment.mesh_list.groups():
                mesh_id = int(mesh.id[...])
                single_mesh_group = single_detail_lvl_group.create_group(mesh_id)

                for mesh_component_name, mesh_component in mesh.groups():
                    if mesh_component_name != "id":
                        write_mesh_component_data_to_zarr_arr(
                            target_group=single_mesh_group,
                            mesh=mesh,
                            mesh_component_name=mesh_component_name,
                            params_for_storing=params_for_storing,
                        )
                # TODO: check in which units is area and volume
                vertices = single_mesh_group["vertices"][...]
                triangles = single_mesh_group["triangles"][...]
                vedo_mesh_obj = Mesh([vertices, triangles])
                single_mesh_group.attrs["num_vertices"] = (
                    single_mesh_group.vertices.attrs["num_vertices"]
                )
                single_mesh_group.attrs["area"] = vedo_mesh_obj.area()
                # single_mesh_group.attrs['volume'] = vedo_mesh_obj.volume()
