# methods for processing volume and segmentation data
from re import L
from vedo import Mesh
import math
import numcodecs
import gemmi
import numpy as np
import zarr

from db.file_system.constants import SEGMENTATION_DATA_GROUPNAME, VOLUME_DATA_GROUPNAME

from preprocessor.src.preprocessors.implementations.sff.preprocessor._segmentation_methods import decode_base64_data
from preprocessor.src.preprocessors.implementations.sff.preprocessor.constants import MESH_VERTEX_DENSITY_THRESHOLD, MIN_GRID_SIZE
from preprocessor.src.preprocessors.implementations.sff.preprocessor._segmentation_methods import \
    map_value_to_segment_id, lattice_data_to_np_arr
from preprocessor.src.preprocessors.implementations.sff.preprocessor._volume_map_methods import read_volume_data
from preprocessor.src.preprocessors.implementations.sff.preprocessor.downsampling.downsampling import \
    compute_number_of_downsampling_steps, compute_vertex_density, create_volume_downsamplings, create_category_set_downsamplings, simplify_meshes, _store_mesh_data_in_zarr
from preprocessor.src.tools.magic_kernel_downsampling_3d.magic_kernel_downsampling_3d import MagicKernel3dDownsampler
from preprocessor.src.preprocessors.implementations.sff.preprocessor.numpy_methods import chunk_numpy_arr
from preprocessor.src.preprocessors.implementations.sff.preprocessor._zarr_methods import create_dataset_wrapper
import dask.array as da

def process_volume_data(zarr_structure: zarr.hierarchy.group, dask_arr: da.Array, params_for_storing: dict, force_dtype: np.dtype):
    '''
    Takes read map object, extracts volume data, downsamples it, stores to zarr_structure
    '''
    volume_data_gr: zarr.hierarchy.group = zarr_structure.create_group(VOLUME_DATA_GROUPNAME)
    volume_arr = dask_arr
    volume_downsampling_steps = compute_number_of_downsampling_steps(
        MIN_GRID_SIZE,
        input_grid_size=math.prod(volume_arr.shape),
        force_dtype=volume_arr.dtype,
        factor=2 ** 3,
        min_downsampled_file_size_bytes=5 * 10 ** 6
    )
    create_volume_downsamplings(
        original_data=volume_arr,
        downsampled_data_group=volume_data_gr,
        downsampling_steps=volume_downsampling_steps,
        params_for_storing=params_for_storing,
        force_dtype=force_dtype
    )


def process_segmentation_data(magic_kernel: MagicKernel3dDownsampler, zarr_structure: zarr.hierarchy.group, mesh_simplification_curve: dict[int, float], params_for_storing: dict) -> None:
    '''
    Extracts segmentation data from lattice, downsamples it, stores to zarr structure
    '''
    segm_data_gr: zarr.hierarchy.group = zarr_structure.create_group(SEGMENTATION_DATA_GROUPNAME)
    if zarr_structure.primary_descriptor[0] == b'three_d_volume':
        process_three_d_volume_segmentation_data(segm_data_gr, magic_kernel, zarr_structure, params_for_storing=params_for_storing)
    elif zarr_structure.primary_descriptor[0] == b'mesh_list':
        process_mesh_segmentation_data(segm_data_gr, zarr_structure, mesh_simplification_curve, params_for_storing=params_for_storing)

def process_three_d_volume_segmentation_data(segm_data_gr: zarr.hierarchy.group, magic_kernel: MagicKernel3dDownsampler, zarr_structure: zarr.hierarchy.group, params_for_storing):
    value_to_segment_id_dict = map_value_to_segment_id(zarr_structure)

    for gr_name, gr in zarr_structure.lattice_list.groups():
        # gr is a 'lattice' obj in lattice list
        lattice_id = int(gr.id[...])
        segm_arr = lattice_data_to_np_arr(
            data=gr.data[0],
            mode=gr.mode[0],
            endianness=gr.endianness[0],
            arr_shape=(gr.size.cols[...], gr.size.rows[...], gr.size.sections[...])
        )
        segmentation_downsampling_steps = compute_number_of_downsampling_steps(
            MIN_GRID_SIZE,
            input_grid_size=math.prod(segm_arr.shape),
            force_dtype=segm_arr.dtype,
            factor=2 ** 3,
            min_downsampled_file_size_bytes=5 * 10 ** 6
        )
        # specific lattice with specific id
        lattice_gr = segm_data_gr.create_group(gr_name)
        create_category_set_downsamplings(
            magic_kernel,
            segm_arr,
            segmentation_downsampling_steps,
            lattice_gr,
            value_to_segment_id_dict[lattice_id],
            params_for_storing=params_for_storing
        )

def _write_mesh_component_data_to_zarr_arr(target_group: zarr.hierarchy.group, mesh: zarr.hierarchy.group, mesh_component_name: str, params_for_storing: dict):
    unchunked_component_data = decode_base64_data(
            data=mesh[mesh_component_name].data[...][0],
            mode=mesh[mesh_component_name].mode[...][0],
            endianness=mesh[mesh_component_name].endianness[...][0]
        )
    # chunked onto triples
    chunked_component_data = chunk_numpy_arr(unchunked_component_data, 3)
    
    component_arr = create_dataset_wrapper(
        zarr_group=target_group,
        data=chunked_component_data,
        name=mesh_component_name,
        shape=chunked_component_data.shape,
        dtype=chunked_component_data.dtype,
        params_for_storing=params_for_storing
    )

    component_arr.attrs[f'num_{mesh_component_name}'] = \
        int(mesh[mesh_component_name][f'num_{mesh_component_name}'][...])



def process_mesh_segmentation_data(segm_data_gr: zarr.hierarchy.group, zarr_structure: zarr.hierarchy.group, simplification_curve: dict[int, float], params_for_storing: dict):

    for segment_name, segment in zarr_structure.segment_list.groups():
        segment_id = str(int(segment.id[...]))
        single_segment_group = segm_data_gr.create_group(segment_id)
        single_detail_lvl_group = single_segment_group.create_group('1')
        if 'mesh_list' in segment:
            for mesh_name, mesh in segment.mesh_list.groups():
                mesh_id = str(int(mesh.id[...]))
                single_mesh_group = single_detail_lvl_group.create_group(mesh_id)

                for mesh_component_name, mesh_component in mesh.groups():
                    if mesh_component_name != 'id':
                        _write_mesh_component_data_to_zarr_arr(
                            target_group=single_mesh_group,
                            mesh=mesh,
                            mesh_component_name=mesh_component_name,
                            params_for_storing=params_for_storing
                        )
                # TODO: check in which units is area and volume
                vertices = single_mesh_group['vertices'][...]
                triangles = single_mesh_group['triangles'][...]
                vedo_mesh_obj = Mesh([vertices, triangles])
                single_mesh_group.attrs['num_vertices'] = single_mesh_group.vertices.attrs['num_vertices']
                single_mesh_group.attrs['area'] = vedo_mesh_obj.area()
                # single_mesh_group.attrs['volume'] = vedo_mesh_obj.volume()
    

    calc_mode = 'area'
    density_threshold = MESH_VERTEX_DENSITY_THRESHOLD[calc_mode]
    
    for segment_name_id, segment in segm_data_gr.groups():
        original_detail_lvl_mesh_list_group = segment['1']
        group_ref = original_detail_lvl_mesh_list_group

        for level, fraction in simplification_curve.items():
            if density_threshold != 0 and compute_vertex_density(group_ref, mode=calc_mode) <= density_threshold:
                break
            if fraction == 1:
                continue  # original data, don't need to compute anything
            mesh_data_dict = simplify_meshes(original_detail_lvl_mesh_list_group, ratio=fraction, segment_id=segment_name_id)
            # TODO: potentially simplify meshes may output mesh with 0 vertices, normals, triangles
            # it should not be stored?
            # check each mesh in mesh_data_dict if it contains 0 vertices
            # remove all such meshes from dict
            for mesh_id in list(mesh_data_dict.keys()):
                if mesh_data_dict[mesh_id]['attrs']['num_vertices'] == 0:
                    del mesh_data_dict[mesh_id]

            # if there is no meshes left in dict - break from while loop
            if not bool(mesh_data_dict):
                break
            
            group_ref = _store_mesh_data_in_zarr(mesh_data_dict, segment, detail_level=level, params_for_storing=params_for_storing)
