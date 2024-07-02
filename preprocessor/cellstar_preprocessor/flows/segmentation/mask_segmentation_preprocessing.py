from pathlib import Path

import mrcfile
import numpy as np
from cellstar_db.models import SegmentationPrimaryDescriptor
from cellstar_preprocessor.flows.constants import LATTICE_SEGMENTATION_DATA_GROUPNAME
from cellstar_preprocessor.flows.segmentation.helper_methods import (
    store_segmentation_data_in_zarr_structure,
)
from cellstar_preprocessor.flows.zarr_methods import open_zarr
from cellstar_preprocessor.model.segmentation import InternalSegmentation


def _normalize_axis_order_mrcfile_numpy(
    arr: np.memmap, mrc_header: object
) -> np.memmap:
    """
    Normalizes axis order to X, Y, Z (1, 2, 3)
    """
    h = mrc_header
    current_order = int(h.mapc) - 1, int(h.mapr) - 1, int(h.maps) - 1

    if current_order != (0, 1, 2):
        print(f"Reordering axes from {current_order}...")
        ao = {v: i for i, v in enumerate(current_order)}
        # TODO: optimize this to a single transpose
        arr = arr.transpose().transpose(ao[2], ao[1], ao[0]).transpose()
    else:
        arr = arr.transpose()

    return arr


def mask_segmentation_preprocessing(s: InternalSegmentation):
    our_zarr_structure = open_zarr(s.path)

    s.primary_descriptor = SegmentationPrimaryDescriptor.three_d_volume

    segmentation_data_gr = our_zarr_structure.create_group(
        LATTICE_SEGMENTATION_DATA_GROUPNAME
    )

    # artificially create value_to_segment_id_dict
    s.value_to_segment_id_dict = {}

    s.set_segmentation_custom_data()

    # should be dict str to str with all channel ids
    if "segmentation_ids_mapping" not in s.custom_data:
        list_of_sesgmentation_pathes: list[Path] = s.input_path
        s.custom_data["segmentation_ids_mapping"] = {
            s.stem: s.stem for s in list_of_sesgmentation_pathes
        }

    segmentation_ids_mapping: dict[str, str] = s.custom_data["segmentation_ids_mapping"]

    # for lattice_id, mask in enumerate(internal_segmentation.segmentation_input_path):
    for mask in s.input_path:
        mask: Path
        lattice_id = segmentation_ids_mapping[mask.stem]
        with mrcfile.open(str(mask.resolve())) as mrc_original:
            data = mrc_original.data
            header = mrc_original.header

            data = _normalize_axis_order_mrcfile_numpy(arr=data, mrc_header=header)
            s.value_to_segment_id_dict[lattice_id] = {}
            s.map_headers[lattice_id] = header

            if data.dtype.kind == "f":
                data.setflags(write=1)
                data = data.astype("i4")

            for value in np.unique(data):
                s.value_to_segment_id_dict[lattice_id][int(value)] = int(value)

            lattice_gr = segmentation_data_gr.create_group(lattice_id)
            params_for_storing = s.params_for_storing

            store_segmentation_data_in_zarr_structure(
                original_data=data,
                lattice_data_group=lattice_gr,
                value_to_segment_id_dict_for_specific_lattice_id=s.value_to_segment_id_dict[
                    lattice_id
                ],
                params_for_storing=params_for_storing,
            )

    print("Mask segmentation processed")
    print(f"Mask headers: {s.map_headers}")
