import nibabel as nib
import numpy as np
from cellstar_preprocessor.flows.constants import LATTICE_SEGMENTATION_DATA_GROUPNAME
# from cellstar_preprocessor.model.segmentation import (
#     store_segmentation_data,
# )
from cellstar_preprocessor.flows.zarr_methods import open_zarr
from cellstar_preprocessor.model.segmentation import InternalSegmentation


def nii_segmentation_preprocessing(internal_segmentation: InternalSegmentation):
    our_zarr_structure = open_zarr(internal_segmentation.path)

    segmentation_data_gr = our_zarr_structure.create_group(
        LATTICE_SEGMENTATION_DATA_GROUPNAME
    )
    internal_segmentation.value_to_segment_id_dict = {}

    # index = 'lattice_id'
    for index, segm_input_path in enumerate(internal_segmentation.input_path):
        img = nib.load(str(segm_input_path.resolve()))
        data = img.get_fdata()
        # temp fix: convert float64 to int
        data = data.astype(np.int32)

        # temp hack to replace segment ids so that it will work for multiple lattices
        #
        if index > 0:
            data[data == 1] = index + 1

        internal_segmentation.value_to_segment_id_dict[index] = {}
        for value in np.unique(data):
            internal_segmentation.value_to_segment_id_dict[index][int(value)] = int(
                value
            )

        # TODO: multiple lattices?
        lattice_gr = segmentation_data_gr.create_group(str(index))
        params_for_storing = internal_segmentation.params_for_storing

        # store_segmentation_data(
        #     prepared_data=data,
        #     segmentation_gr=lattice_gr,
        #     value_to_segment_id_dict_for_specific_segmentation_id=internal_segmentation.value_to_segment_id_dict[
        #         index
        #     ],
        #     params_for_storing=params_for_storing,
        # )
