from pathlib import Path
from cellstar_db.models import SegmentationPrimaryDescriptor
from cellstar_preprocessor.flows.segmentation.helper_methods import store_segmentation_data_in_zarr_structure
# from cellstar_preprocessor.model.input import SegmentationPrimaryDescriptor
from cellstar_preprocessor.model.segmentation import InternalSegmentation
from cellstar_preprocessor.tools.tiff_stack_to_da_arr.tiff_stack_to_da_arr import tiff_stack_to_da_arr
import numpy as np
import zarr
import dask.array as da

from cellstar_preprocessor.flows.common import (
    open_zarr_structure_from_path,
    prepare_ometiff_for_writing,
    read_ometiff_to_dask,
    set_ometiff_source_metadata,
    set_segmentation_custom_data,
    set_volume_custom_data,
)
from cellstar_preprocessor.flows.constants import LATTICE_SEGMENTATION_DATA_GROUPNAME, VOLUME_DATA_GROUPNAME
from cellstar_preprocessor.flows.volume.helper_methods import (
    store_volume_data_in_zarr_stucture,
)
from cellstar_preprocessor.model.volume import InternalVolume

# from cellstar_preprocessor.tools.tiff_stack_to_da_arr.tiff_stack_to_da_arr import tiff_stack_to_da_arr

def tiff_segmentation_stack_dir_processing(internal_segmentation: InternalSegmentation):
    our_zarr_structure = open_zarr_structure_from_path(
        internal_segmentation.intermediate_zarr_structure_path
    )
    
    img_array = tiff_stack_to_da_arr(internal_segmentation.segmentation_input_path)

    
    
    internal_segmentation.primary_descriptor = (
        SegmentationPrimaryDescriptor.three_d_volume
    )

    segmentation_data_gr = our_zarr_structure.create_group(
        LATTICE_SEGMENTATION_DATA_GROUPNAME
    )

    # artificially create value_to_segment_id_dict
    internal_segmentation.value_to_segment_id_dict = {}

    set_segmentation_custom_data(internal_segmentation, our_zarr_structure)

    
    # should be dict str to str with all channel ids
    if "segmentation_ids_mapping" not in internal_segmentation.custom_data:
        # list_of_sesgmentation_pathes: list[Path] = (
        #     internal_segmentation.segmentation_input_path
        # )
        internal_segmentation.custom_data["segmentation_ids_mapping"] = {
            internal_segmentation.segmentation_input_path.stem: internal_segmentation.segmentation_input_path.stem
            # s.stem: s.stem for s in list_of_sesgmentation_pathes
        }

    segmentation_ids_mapping: dict[str, str] = internal_segmentation.custom_data[
        "segmentation_ids_mapping"
    ]

    lattice_id = segmentation_ids_mapping[internal_segmentation.segmentation_input_path.stem]
    lattice_gr = segmentation_data_gr.create_group(lattice_id)
    params_for_storing = internal_segmentation.params_for_storing
    
    
    internal_segmentation.value_to_segment_id_dict[lattice_id] = {}
    
    for value in np.unique(img_array.compute()):
        internal_segmentation.value_to_segment_id_dict[lattice_id][
            int(value)
        ] = int(value)
    
    
    # TODO: dask array to memmap
    store_segmentation_data_in_zarr_structure(
        original_data=img_array.compute(),
        lattice_data_group=lattice_gr,
        value_to_segment_id_dict_for_specific_lattice_id=internal_segmentation.value_to_segment_id_dict[
            lattice_id
        ],
        params_for_storing=params_for_storing,
    )

    print("Mask segmentation processed")
    print(f"Mask headers: {internal_segmentation.map_headers}")