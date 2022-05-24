# methods for processing volume and segmentation data
import math

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
