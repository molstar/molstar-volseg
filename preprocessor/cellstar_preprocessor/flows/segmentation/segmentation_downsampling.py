import math

import numpy as np
import zarr
from cellstar_db.models import SegmentationPrimaryDescriptor
from cellstar_preprocessor.flows.common import (
    compute_downsamplings_to_be_stored,
    compute_number_of_downsampling_steps,
)
from cellstar_preprocessor.flows.constants import (
    LATTICE_SEGMENTATION_DATA_GROUPNAME,
    MESH_SEGMENTATION_DATA_GROUPNAME,
    MESH_VERTEX_DENSITY_THRESHOLD,
    MIN_GRID_SIZE,
)
from cellstar_preprocessor.flows.segmentation.category_set_downsampling_methods import (
    downsample_categorical_data,
    store_downsampling_levels_in_zarr,
)
from cellstar_preprocessor.flows.segmentation.downsampling_level_dict import (
    DownsamplingLevelDict,
)
from cellstar_preprocessor.flows.segmentation.helper_methods import (
    compute_vertex_density,
    simplify_meshes,
    store_mesh_data_in_zarr,
)
from cellstar_preprocessor.flows.segmentation.segmentation_set_table import (
    SegmentationSetTable,
)
from cellstar_preprocessor.flows.zarr_methods import open_zarr
from cellstar_preprocessor.model.segmentation import InternalSegmentation
from cellstar_preprocessor.tools.magic_kernel_downsampling_3d.magic_kernel_downsampling_3d import (
    MagicKernel3dDownsampler,
)


def segmentation_downsampling(internal_segmentation: InternalSegmentation):
    zarr_structure = open_zarr(internal_segmentation.path)
    if (
        internal_segmentation.primary_descriptor
        == SegmentationPrimaryDescriptor.three_d_volume
    ):
        for lattice_gr_name, lattice_gr in zarr_structure[
            LATTICE_SEGMENTATION_DATA_GROUPNAME
        ].groups():
            original_res_gr: zarr.Group = lattice_gr["1"]
            for time, time_gr in original_res_gr.groups():
                original_data_arr = original_res_gr[time].grid
                lattice_id = lattice_gr_name

                segmentation_downsampling_steps = compute_number_of_downsampling_steps(
                    int_vol_or_seg=internal_segmentation,
                    min_grid_size=MIN_GRID_SIZE,
                    input_grid_size=math.prod(original_data_arr.shape),
                    force_dtype=original_data_arr.dtype,
                    factor=2**3,
                )

                ratios_to_be_stored = compute_downsamplings_to_be_stored(
                    int_vol_or_seg=internal_segmentation,
                    number_of_downsampling_steps=segmentation_downsampling_steps,
                    input_grid_size=math.prod(original_data_arr.shape),
                    dtype=original_data_arr.dtype,
                    factor=2**3,
                )

                _create_category_set_downsamplings(
                    magic_kernel=MagicKernel3dDownsampler(),
                    original_data=original_data_arr[...],
                    downsampling_steps=segmentation_downsampling_steps,
                    ratios_to_be_stored=ratios_to_be_stored,
                    data_group=lattice_gr,
                    value_to_segment_id_dict_for_specific_lattice_id=internal_segmentation.value_to_segment_id_dict[
                        lattice_id
                    ],
                    params_for_storing=internal_segmentation.params_for_storing,
                    time_frame=time,
                )

        # NOTE: removes original level resolution data
        if internal_segmentation.downsampling_parameters.remove_original_resolution:
            del lattice_gr[1]
            print("Original resolution data removed for segmentation")

    elif (
        internal_segmentation.primary_descriptor
        == SegmentationPrimaryDescriptor.mesh_list
    ):
        simplification_curve: dict[int, float] = (
            internal_segmentation.simplification_curve
        )
        calc_mode = "area"
        density_threshold = MESH_VERTEX_DENSITY_THRESHOLD[calc_mode]
        # mesh set_id => timeframe => segment_id => detail_lvl => mesh_id in meshlist

        segm_data_gr = zarr_structure[MESH_SEGMENTATION_DATA_GROUPNAME]
        for set_id, set_gr in segm_data_gr.groups():
            for timeframe_index, timeframe_gr in set_gr.groups():
                for segment_name_id, segment in timeframe_gr.groups():
                    original_detail_lvl_mesh_list_group = segment[1]
                    group_ref = original_detail_lvl_mesh_list_group

                    for level, fraction in simplification_curve.items():
                        if (
                            density_threshold != 0
                            and compute_vertex_density(group_ref, mode=calc_mode)
                            <= density_threshold
                        ):
                            break
                        if fraction == 1:
                            continue  # original data, don't need to compute anything
                        mesh_data_dict = simplify_meshes(
                            original_detail_lvl_mesh_list_group,
                            ratio=fraction,
                            segment_id=segment_name_id,
                        )
                        # TODO: potentially simplify meshes may output mesh with 0 vertices, normals, triangles
                        # it should not be stored?
                        # check each mesh in mesh_data_dict if it contains 0 vertices
                        # remove all such meshes from dict
                        for mesh_id in list(mesh_data_dict.keys()):
                            if mesh_data_dict[mesh_id]["attrs"]["num_vertices"] == 0:
                                del mesh_data_dict[mesh_id]

                        # if there is no meshes left in dict - break from while loop
                        if not bool(mesh_data_dict):
                            break

                        # mesh set_id => timeframe => segment_id => detail_lvl => mesh_id in meshlist
                        group_ref = store_mesh_data_in_zarr(
                            mesh_data_dict,
                            segment,
                            detail_level=level,
                            params_for_storing=internal_segmentation.params_for_storing,
                        )

                    # segment[1]
                    # NOTE: removes original level resolution data
                    if (
                        internal_segmentation.downsampling_parameters.remove_original_resolution
                    ):
                        del segment[1]
                        # print("Original resolution data removed for segmentation")
        if internal_segmentation.downsampling_parameters.remove_original_resolution:
            # del internal_segmentation.simplification_curve[1]
            internal_segmentation.simplification_curve.pop(1, None)

    print("Segmentation downsampled")


def _create_category_set_downsamplings(
    *,
    magic_kernel: MagicKernel3dDownsampler,
    original_data: np.ndarray,
    downsampling_steps: int,
    ratios_to_be_stored: list,
    data_group: zarr.Group,
    value_to_segment_id_dict_for_specific_lattice_id: dict,
    params_for_storing: dict,
    time_frame: int,
):
    """
    Take original segmentation data, do all downsampling levels, create zarr datasets for each
    """
    # table with just singletons, e.g. "104": {104}, "94" :{94}
    initial_set_table = SegmentationSetTable(
        original_data, value_to_segment_id_dict_for_specific_lattice_id
    )

    # for now contains just x1 downsampling lvl dict, in loop new dicts for new levels are appended
    levels = [
        DownsamplingLevelDict(
            {"ratio": 1, "grid": original_data, "set_table": initial_set_table}
        )
    ]
    for i in range(downsampling_steps):
        current_set_table = SegmentationSetTable(
            original_data, value_to_segment_id_dict_for_specific_lattice_id
        )
        # on first iteration (i.e. when doing x2 downsampling), it takes original_data and initial_set_table with set of singletons
        levels.append(
            downsample_categorical_data(magic_kernel, levels[i], current_set_table)
        )

    # remove original data, as they are already stored
    levels.pop(0)
    # remove all with ratios that are not in ratios_to_be_stored
    levels = [level for level in levels if level.get_ratio() in ratios_to_be_stored]
    # store levels list in zarr structure (can be separate function)
    store_downsampling_levels_in_zarr(
        levels,
        lattice_data_group=data_group,
        params_for_storing=params_for_storing,
        time_frame=time_frame,
    )
