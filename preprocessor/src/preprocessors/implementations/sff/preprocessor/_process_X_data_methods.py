# methods for processing volume and segmentation data
import math
import numcodecs
import gemmi
import numpy as np
import zarr

from preprocessor.src.preprocessors.implementations.sff.preprocessor.constants import SEGMENTATION_DATA_GROUPNAME, \
    VOLUME_DATA_GROUPNAME, MIN_GRID_SIZE
from preprocessor.src.preprocessors.implementations.sff.preprocessor._segmentation_methods import \
    map_value_to_segment_id, lattice_data_to_np_arr
from preprocessor.src.preprocessors.implementations.sff.preprocessor._volume_map_methods import read_volume_data
from preprocessor.src.preprocessors.implementations.sff.preprocessor.downsampling.downsampling import \
    compute_number_of_downsampling_steps, create_volume_downsamplings, create_category_set_downsamplings
from preprocessor.src.tools.magic_kernel_downsampling_3d.magic_kernel_downsampling_3d import MagicKernel3dDownsampler


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
    if zarr_structure.primary_descriptor[0] == 'three_d_volume':
        process_three_d_volume_segmentation_data(segm_data_gr, magic_kernel, zarr_structure)
    elif zarr_structure.primary_descriptor[0] == 'mesh_list':
        process_mesh_segmentation_data(segm_data_gr, magic_kernel, zarr_structure)

def process_three_d_volume_segmentation_data(segm_data_gr: zarr.hierarchy.group, magic_kernel: MagicKernel3dDownsampler, zarr_structure: zarr.hierarchy.group):
    value_to_segment_id_dict = map_value_to_segment_id(zarr_structure)

    for gr_name, gr in zarr_structure.lattice_list.groups():
        # gr is a 'lattice' obj in lattice list
        lattice_id = int(gr.id[...])
        segm_arr = lattice_data_to_np_arr(
            gr.data[0],
            gr.mode[0],
            (gr.size.cols[...], gr.size.rows[...], gr.size.sections[...])
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

def process_mesh_segmentation_data(segm_data_gr: zarr.hierarchy.group, magic_kernel: MagicKernel3dDownsampler, zarr_structure: zarr.hierarchy.group):
    d = {}
    for segment_name, segment in zarr_structure.segment_list.groups():
        # TODO: store triangle count in metadata
        # TODO: decode data of .vertices, .triangles, etc.
        d[segment.id] = []
        for mesh_name, mesh in segment.mesh_list.groups():
            # indeces of vertices
            triangles = decode_zlib_base64_data(mesh.triangles.data, mesh.triangles.mode)
            vertices = decode_zlib_base64_data(mesh.vertices.data, mesh.vertices.mode)
            mesh_obj  = {
                triangles: triangles,
                vertices: vertices,
            }
            d[segment.id].append(mesh_obj)
            

    arr = segm_data_gr.create_dataset(
            # TODO: think about name (downsampling lvl e.g.)
            name='mesh_segmentation',
            dtype=object,
            object_codec=numcodecs.JSON(),
            shape=1
        )
    
    arr[...] = [d]
    # TODO: create simplified meshes as downsamplings