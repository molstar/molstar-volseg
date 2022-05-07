def __store_downsampling_levels_in_zarr_structure(self, levels_list: List[DownsamplingLevelDict], downsampled_data_group: zarr.hierarchy.Group):
    for level_dict in levels_list:
        grid = level_dict.get_grid()
        table = level_dict.get_set_table()
        ratio = level_dict.get_ratio()

        new_level_group: zarr.hierarchy.Group = downsampled_data_group.create_group(str(ratio))
        grid_arr = new_level_group.create_dataset(
            data=grid,
            name='grid',
            shape=grid.shape,
            dtype=grid.dtype,
            # # TODO: figure out how to determine optimal chunk size depending on the data
            chunks=(25, 25, 25)
        )
        
        table_obj_arr = new_level_group.create_dataset(
            # be careful here, encoding JSON, sets need to be converted to lists
            name='set_table',
            # MsgPack leads to bug/error: int is not allowed for map key when strict_map_key=True
            dtype=object,
            object_codec=numcodecs.JSON(),
            shape=1
        )

        table_obj_arr[...] = [table.get_serializable_repr()]

def __downsample_categorical_data_using_category_sets(self, previous_level_dict: DownsamplingLevelDict, current_set_table: SegmentationSetTable) -> DownsamplingLevelDict:
    '''
    Downsample data returning a dict for that level containing new grid and a set table for that level
    '''
    previous_level_grid: np.ndarray = previous_level_dict.get_grid()
    previous_level_set_table: SegmentationSetTable = previous_level_dict.get_set_table()
    current_level_grid: np.ndarray = create_x2_downsampled_grid(previous_level_grid.shape, np.nan)

    # Select block
    # The following will not work for e.g. 5**3 grid, as block size = 2,2,2
    # blocks: np.ndarray = view_as_blocks(previous_level_grid, (2, 2, 2))
    # instead, get target voxels, e.g. for 1st block it is *0,0,0) voxel
    target_voxels_coords = np.array(extract_target_voxels_coords(previous_level_grid.shape))
    origin_coords = np.array([0, 0, 0])
    max_coords = np.subtract(previous_level_grid.shape, (1, 1, 1))
    # loop over voxels, c = coords of a single voxel
    for start_coords in target_voxels_coords:
        # end coords for start_coords 0,0,0 are 2,2,2
        # (it will actually select from 0,0,0 to 1,1,1 as slicing end index is non-inclusive)
        end_coords = start_coords + 2
        if (end_coords < origin_coords).any():
            end_coords = np.fmax(end_coords, origin_coords)
        if (end_coords > max_coords).any():
            end_coords = np.fmin(end_coords, max_coords)
        
        block: np.ndarray = previous_level_grid[
            start_coords[0] : end_coords[0],
            start_coords[1] : end_coords[1],
            start_coords[2] : end_coords[2]
        ]

        new_id: int = self.__downsample_2x2x2_categorical_block(block, current_set_table, previous_level_set_table)
        # putting that id in the location of new grid corresponding to that block
        current_level_grid[
            round(start_coords[0] / 2),
            round(start_coords[1] / 2),
            round(start_coords[2] / 2)
        ] = new_id
    
    # need to check before conversion to int as in int grid nans => some guge number
    assert np.isnan(current_level_grid).any() == False, f'Segmentation grid contain NAN values'

    current_level_grid = current_level_grid.astype(np.int32)
    # write grid into 'grid' key of new level dict
    # add current level set table to new level dict
    new_dict = DownsamplingLevelDict({
        'ratio': round(previous_level_dict.get_ratio() * 2),
        'grid': current_level_grid,
        'set_table': current_set_table
        })
    # and return that dict (will have a new grid and a new set table)  
    return new_dict
    

def __downsample_2x2x2_categorical_block(self, block: np.ndarray, current_table: SegmentationSetTable, previous_table: SegmentationSetTable) -> int:
    potentially_new_category: Set = self.__compute_union(block, previous_table)
    category_id: int = current_table.resolve_category(potentially_new_category)
    return category_id


def __compute_union(self, block: np.ndarray, previous_table: SegmentationSetTable) -> Set:
    # in general, where x y z are sets
    # result = x.union(y, z) 
    block_values: Tuple = tuple(block.flatten())
    categories: Tuple = previous_table.get_categories(block_values)
    union: Set = set().union(*categories)
    return union
