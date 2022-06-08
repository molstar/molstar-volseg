# methods for processing volume and segmentation data
from re import L
from vedo import Mesh
import math
import numcodecs
import gemmi
import numpy as np
import zarr
from preprocessor.src.preprocessors.implementations.sff.preprocessor._segmentation_methods import decode_base64_data
from preprocessor.src.preprocessors.implementations.sff.preprocessor.constants import MESH_SIMPLIFICATION_CURVE, MESH_VERTEX_DENSITY_THRESHOLD, SEGMENTATION_DATA_GROUPNAME, \
    VOLUME_DATA_GROUPNAME, MIN_GRID_SIZE
from preprocessor.src.preprocessors.implementations.sff.preprocessor._segmentation_methods import \
    map_value_to_segment_id, lattice_data_to_np_arr
from preprocessor.src.preprocessors.implementations.sff.preprocessor._volume_map_methods import read_volume_data
from preprocessor.src.preprocessors.implementations.sff.preprocessor.downsampling.downsampling import \
    compute_number_of_downsampling_steps, compute_vertex_density, create_volume_downsamplings, create_category_set_downsamplings, simplify_meshes, _store_mesh_data_in_zarr
from preprocessor.src.tools.magic_kernel_downsampling_3d.magic_kernel_downsampling_3d import MagicKernel3dDownsampler
from preprocessor.src.preprocessors.implementations.sff.preprocessor.numpy_methods import chunk_numpy_arr

def process_volume_data(zarr_structure: zarr.hierarchy.group, map_object: gemmi.Ccp4Map, force_dtype=np.float32):
    '''
    Takes read map object, extracts volume data, downsamples it, stores to zarr_structure
    '''
    volume_data_gr: zarr.hierarchy.group = zarr_structure.create_group(VOLUME_DATA_GROUPNAME)
    volume_arr = read_volume_data(map_object, force_dtype)
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
        force_dtype=force_dtype
    )


def process_segmentation_data(magic_kernel: MagicKernel3dDownsampler, zarr_structure: zarr.hierarchy.group) -> None:
    '''
    Extracts segmentation data from lattice, downsamples it, stores to zarr structure
    '''
    segm_data_gr: zarr.hierarchy.group = zarr_structure.create_group(SEGMENTATION_DATA_GROUPNAME)
    if zarr_structure.primary_descriptor[0] == b'three_d_volume':
        process_three_d_volume_segmentation_data(segm_data_gr, magic_kernel, zarr_structure)
    elif zarr_structure.primary_descriptor[0] == b'mesh_list':
        process_mesh_segmentation_data(segm_data_gr, magic_kernel, zarr_structure)

def process_three_d_volume_segmentation_data(segm_data_gr: zarr.hierarchy.group, magic_kernel: MagicKernel3dDownsampler, zarr_structure: zarr.hierarchy.group):
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
            value_to_segment_id_dict[lattice_id]
        )

def _write_mesh_component_data_to_zarr_arr(target_group: zarr.hierarchy.group, mesh: zarr.hierarchy.group, mesh_component_name: str):
    unchunked_component_data = decode_base64_data(
            data=mesh[mesh_component_name].data[...][0],
            mode=mesh[mesh_component_name].mode[...][0],
            endianness=mesh[mesh_component_name].endianness[...][0]
        )
    # chunked onto triples
    chunked_component_data = chunk_numpy_arr(unchunked_component_data, 3)
    component_arr = target_group.create_dataset(
        data=chunked_component_data,
        name=mesh_component_name,
        shape=chunked_component_data.shape,
        dtype=chunked_component_data.dtype,
    )
    component_arr.attrs[f'num_{mesh_component_name}'] = \
        int(mesh[mesh_component_name][f'num_{mesh_component_name}'][...])



def process_mesh_segmentation_data(segm_data_gr: zarr.hierarchy.group, magic_kernel: MagicKernel3dDownsampler, zarr_structure: zarr.hierarchy.group):

    for segment_name, segment in zarr_structure.segment_list.groups():
        segment_id = str(int(segment.id[...]))
        single_segment_group = segm_data_gr.create_group(segment_id)
        single_detail_lvl_group = single_segment_group.create_group('1')
        for mesh_name, mesh in segment.mesh_list.groups():
            mesh_id = str(int(mesh.id[...]))
            single_mesh_group = single_detail_lvl_group.create_group(mesh_id)
            
            

            for mesh_component_name, mesh_component in mesh.groups():
                if mesh_component_name != 'id':
                    _write_mesh_component_data_to_zarr_arr(
                        target_group=single_mesh_group,
                        mesh=mesh,
                        mesh_component_name=mesh_component_name
                    )
            # TODO: check in which units is area and volume
            vertices = single_mesh_group['vertices'][...]
            triangles = single_mesh_group['triangles'][...]
            vedo_mesh_obj = Mesh([vertices, triangles])
            single_mesh_group.attrs['num_vertices'] = single_mesh_group.vertices.attrs['num_vertices']
            single_mesh_group.attrs['area'] = vedo_mesh_obj.area()
            single_mesh_group.attrs['volume'] = vedo_mesh_obj.volume()
    

    calc_mode = 'area'
    for segment_name_id, segment in segm_data_gr.groups():
        for detail_lvl, mesh_list_group in segment.groups():
            
            for ratio in MESH_SIMPLIFICATION_CURVE:
                if compute_vertex_density(mesh_list_group, mode = calc_mode) > MESH_VERTEX_DENSITY_THRESHOLD[calc_mode]:
                    # dict with mesh data for that mesh list group
                    mesh_data_dict = simplify_meshes(mesh_list_group, ratio, segment_id=segment_name_id)
                    _store_mesh_data_in_zarr(mesh_data_dict, segment, ratio)
