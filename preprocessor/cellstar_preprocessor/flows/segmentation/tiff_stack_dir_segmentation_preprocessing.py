import numpy as np
from cellstar_db.models import SegmentationPrimaryDescriptor
from cellstar_preprocessor.flows.constants import LATTICE_SEGMENTATION_DATA_GROUPNAME
from cellstar_preprocessor.flows.segmentation.helper_methods import (
    store_segmentation_data_in_zarr_structure,
)

# from cellstar_preprocessor.model.input import SegmentationPrimaryDescriptor
from cellstar_preprocessor.model.segmentation import InternalSegmentation
from cellstar_preprocessor.tools.tiff_stack_to_da_arr.tiff_stack_to_da_arr import (
    tiff_stack_to_da_arr,
)

# from cellstar_preprocessor.tools.tiff_stack_to_da_arr.tiff_stack_to_da_arr import tiff_stack_to_da_arr


def tiff_stack_dir_segmentation_preprocessing(i: InternalSegmentation):
    root = i.get_zarr_root()

    img_array = tiff_stack_to_da_arr(i.input_path)

    i.primary_descriptor = (
        SegmentationPrimaryDescriptor.three_d_volume
    )

    segmentation_data_gr = root.create_group(
        LATTICE_SEGMENTATION_DATA_GROUPNAME
    )

    # artificially create value_to_segment_id_dict
    i.value_to_segment_id_dict = {}

    i.set_segmentation_custom_data()

    # should be dict str to str with all channel ids
    if i.custom_data.segmentation_ids_mapping is None:
        # list_of_sesgmentation_pathes: list[Path] = (
        #     internal_segmentation.segmentation_input_path
        # )
        i.custom_data.segmentation_ids_mapping = {
            i.input_path.stem: i.input_path.stem
            # s.stem: s.stem for s in list_of_sesgmentation_pathes
        }

    segmentation_ids_mapping: dict[str, str] = i.custom_data.segmentation_ids_mapping

    lattice_id = segmentation_ids_mapping[
        i.input_path.stem
    ]
    lattice_gr = segmentation_data_gr.create_group(lattice_id)
    params_for_storing = i.params_for_storing

    i.value_to_segment_id_dict[lattice_id] = {}

    for value in np.unique(img_array.compute()):
        i.value_to_segment_id_dict[lattice_id][int(value)] = int(
            value
        )

    # TODO: dask array to memmap
    store_segmentation_data_in_zarr_structure(
        original_data=img_array.compute(),
        lattice_data_group=lattice_gr,
        value_to_segment_id_dict_for_specific_lattice_id=i.value_to_segment_id_dict[
            lattice_id
        ],
        params_for_storing=params_for_storing,
    )

    print("Mask segmentation processed")
    print(f"Mask headers: {i.map_headers}")
