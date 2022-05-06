# methods for processing volume and segmentation data

def process_volume_data(self, zarr_structure: zarr.hierarchy.group, map_object: gemmi.Ccp4Map, force_dtype=np.float32):
    '''
    Takes read map object, extracts volume data, downsamples it, stores to zarr_structure
    '''
    volume_data_gr: zarr.hierarchy.group = zarr_structure.create_group(VOLUME_DATA_GROUPNAME)        
    volume_arr = self.__read_volume_data(map_object, force_dtype)
    volume_downsampling_steps = self.__compute_number_of_downsampling_steps(
        MIN_GRID_SIZE,
        input_grid_size=math.prod(volume_arr.shape)
    )
    self.__create_volume_downsamplings(
        original_data=volume_arr,
        downsampled_data_group=volume_data_gr,
        downsampling_steps = volume_downsampling_steps,
        force_dtype = force_dtype
    )

def process_segmentation_data(self, zarr_structure: zarr.hierarchy.group) -> None:
    '''
    Extracts segmentation data from lattice, downsamples it, stores to zarr structure
    '''
    segm_data_gr: zarr.hierarchy.group = zarr_structure.create_group(SEGMENTATION_DATA_GROUPNAME)
    value_to_segment_id_dict = self.__create_value_to_segment_id_mapping(zarr_structure)

    for gr_name, gr in zarr_structure.lattice_list.groups():
        # gr is a 'lattice' obj in lattice list
        lattice_id = int(gr.id[...])
        segm_arr = self.__lattice_data_to_np_arr(
            gr.data[0],
            gr.mode[0],
            (gr.size.cols[...], gr.size.rows[...], gr.size.sections[...])
        )
        segmentation_downsampling_steps = self.__compute_number_of_downsampling_steps(
            MIN_GRID_SIZE,
            input_grid_size=math.prod(segm_arr.shape)
        )
        # specific lattice with specific id
        lattice_gr = segm_data_gr.create_group(gr_name)
        self.__create_category_set_downsamplings(
            original_data = segm_arr,
            downsampled_data_group=lattice_gr,
            downsampling_steps = segmentation_downsampling_steps,
            value_to_segment_id_dict_for_specific_lattice_id = value_to_segment_id_dict[lattice_id]
        )
