from cellstar_db.models import DownsamplingLevelDict, StoringParams
import numcodecs
import numpy as np
import zarr
from cellstar_db.models import (
    SegmentationSetTable,
)
from cellstar_preprocessor.flows.zarr_methods import create_dataset_wrapper
from cellstar_preprocessor.tools.magic_kernel_downsampling_3d.magic_kernel_downsampling_3d import (
    MagicKernel3dDownsampler,
)


def store_downsampling_levels_in_zarr(
    levels: list[DownsamplingLevelDict],
    lattice_data_group: zarr.Group,
    params_for_storing: StoringParams,
    time_frame: str,
):
    for d in levels:
        grid = d.grid
        table = d.set_table
        ratio = d.ratio

        new_level_group: zarr.Group = lattice_data_group.create_group(str(ratio))
        time_frame_data_group = new_level_group.create_group(time_frame)

        grid_arr = create_dataset_wrapper(
            zarr_group=time_frame_data_group,
            data=grid,
            name="grid",
            shape=grid.shape,
            dtype=grid.dtype,
            params_for_storing=params_for_storing,
        )

        table_obj_arr = time_frame_data_group.create_dataset(
            # be careful here, encoding JSON, sets need to be converted to lists
            name="set_table",
            # MsgPack leads to bug/error: int is not allowed for map key when strict_map_key=True
            dtype=object,
            object_codec=numcodecs.JSON(),
            shape=1,
        )

        # TODO: use zattrs instead
        table_obj_arr[...] = [table.get_serializable_repr()]


def downsample_categorical_data(
    magic_kernel: MagicKernel3dDownsampler,
    previous_level_dict: DownsamplingLevelDict,
    current_set_table: SegmentationSetTable,
) -> DownsamplingLevelDict:
    """
    Downsample data returning a dict for that level containing new grid and a set table for that level
    """
    previous_level_grid: np.ndarray = previous_level_dict.get_grid()
    previous_level_set_table: SegmentationSetTable = previous_level_dict.get_set_table()
    current_level_grid: np.ndarray = magic_kernel.create_x2_downsampled_grid(
        previous_level_grid.shape, np.nan, dtype=previous_level_grid.dtype
    )

    # Select block
    # The following will not work for e.g. 5**3 grid, as block size = 2,2,2
    # blocks: np.ndarray = view_as_blocks(previous_level_grid, (2, 2, 2))
    # instead, get target voxels, e.g. for 1st block it is *0,0,0) voxel
    target_voxels_coords = np.array(
        magic_kernel.extract_target_voxels_coords(previous_level_grid.shape)
    )
    origin_coords = np.array([0, 0, 0])
    max_coords = np.subtract(previous_level_grid.shape, (1, 1, 1))
    # loop over voxels, c = coords of a single voxel
    for start_coords in target_voxels_coords:
        end_coords = start_coords + 2
        if (end_coords < origin_coords).any():
            end_coords = np.fmax(end_coords, origin_coords)
        if (end_coords > max_coords).any():
            end_coords = np.fmin(end_coords, max_coords)

        block: np.ndarray = previous_level_grid[
            start_coords[0] : end_coords[0],
            start_coords[1] : end_coords[1],
            start_coords[2] : end_coords[2],
        ]

        # exclude block if any dimension = 0
        if any(i == 0 for i in block.shape):
            continue

        new_id: int = downsample_2x2x2_block(
            block, current_set_table, previous_level_set_table
        )
        # putting that id in the location of new grid corresponding to that block
        current_level_grid[
            round(start_coords[0] / 2),
            round(start_coords[1] / 2),
            round(start_coords[2] / 2),
        ] = new_id

    # need to check before conversion to int as in int grid nans => some guge number
    assert (
        np.isnan(current_level_grid).any() == False
    ), f"Segmentation grid contain NAN values"

    # write grid into 'grid' key of new level dict
    # add current level set table to new level dict
    new_dict = DownsamplingLevelDict(
        {
            "ratio": round(previous_level_dict.get_ratio() * 2),
            "grid": current_level_grid,
            "set_table": current_set_table,
        }
    )
    # and return that dict (will have a new grid and a new set table)
    return new_dict


def downsample_2x2x2_block(
    block: np.ndarray,
    current_table: SegmentationSetTable,
    previous_table: SegmentationSetTable,
) -> int:
    # TODO: can try to optimize compute_union
    # by changing its args to block, categories
    # i.e. get categories ouside the function and pass it in
    # as numpy arrays

    potentially_new_category: set = compute_union(block, previous_table)
    category_id: int = current_table.resolve_category(potentially_new_category)
    return category_id


def compute_union(block: np.ndarray, previous_table: SegmentationSetTable) -> set:
    # in general, where x y z are sets
    # result = x.union(y, z)
    block_values: tuple = tuple(block.flatten())
    categories: tuple = previous_table.get_categories(block_values)
    union: set = set().union(*categories)
    return union
