import math

import numpy as np
import zarr
from cellstar_preprocessor.flows.common import (
    compute_downsamplings_to_be_stored,
    compute_number_of_downsampling_steps,
)
from cellstar_preprocessor.flows.constants import (
    LATTICE_SEGMENTATION_DATA_GROUPNAME,
    MIN_GRID_SIZE,
)
from cellstar_preprocessor.flows.segmentation.category_set_downsampling_methods import (
    downsample_categorical_data,
    store_downsampling_levels_in_zarr,
)
# from cellstar_preprocessor.flows.segmentation.downsampling_level_dict import (
#     DownsamplingLevelDict,
# )
from cellstar_db.models import (
    SegmentationSetTable,
)
from cellstar_preprocessor.flows.zarr_methods import open_zarr
from cellstar_preprocessor.model.segmentation import InternalSegmentation
from cellstar_preprocessor.tools.magic_kernel_downsampling_3d.magic_kernel_downsampling_3d import (
    MagicKernel3dDownsampler,
)


def nii_segmentation_downsampling(internal_segmentation: InternalSegmentation):
    zarr_structure = open_zarr(internal_segmentation.path)
    for lattice_gr_name, lattice_gr in zarr_structure[
        LATTICE_SEGMENTATION_DATA_GROUPNAME
    ].groups():
        original_data_arr = lattice_gr["1"]["0"]["0"].grid
        lattice_id = int(lattice_gr_name)

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
            time_frame="0",
            channel="0",
        )

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
    time_frame: str,
    channel: str
):
    """
    Take original segmentation data, do all downsampling levels, create zarr datasets for each
    """
    # table with just singletons, e.g. "104": {104}, "94" :{94}
    initial_set_table = SegmentationSetTable(
        original_data, value_to_segment_id_dict_for_specific_lattice_id
    )

    # for now contains just x1 downsampling lvl dict, in loop new dicts for new levels are appended
    # levels = [
    #     DownsamplingLevelDict(
    #         {"ratio": 1, "grid": original_data, "set_table": initial_set_table}
    #     )
    # ]
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
        channel=channel,
    )
