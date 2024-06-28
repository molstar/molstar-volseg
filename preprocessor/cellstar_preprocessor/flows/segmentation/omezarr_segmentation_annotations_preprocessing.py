from uuid import uuid4

import zarr
import zarr.storage
from cellstar_db.models import (
    AnnotationsMetadata,
    DescriptionData,
    SegmentAnnotationData,
    TargetId,
)
from cellstar_preprocessor.flows.common import open_zarr_structure_from_path
from cellstar_preprocessor.flows.constants import LATTICE_SEGMENTATION_DATA_GROUPNAME
from cellstar_preprocessor.model.segmentation import InternalSegmentation


def _get_label_time(label_value: int, our_label_gr: zarr.Group):
    timeframes_with_present_label = []
    # PLAN:
    # take first available resolution
    available_resolutions = sorted(our_label_gr.group_keys())
    first_resolution = available_resolutions[0]
    # loop over timeframes
    first_resolution_gr = our_label_gr[first_resolution]
    for timeframe_index, timeframe_gr in first_resolution_gr.groups():
        set_table: dict = timeframe_gr.set_table[...][0]

        # present_labels = np.unique(data[...])
        present_labels = [int(i) for i in sorted(set_table.keys())]

        # if label is in present_labels
        # push timeframe index to timeframes_with_present_label
        if label_value in present_labels:
            timeframes_with_present_label.append(int(timeframe_index))

    # at the end, if len(timeframes_with_present_label) == 1
    # => return timeframes_with_present_label[0]
    # else return timeframes_with_present_label

    if len(timeframes_with_present_label) == 1:
        return timeframes_with_present_label[0]
    else:
        return timeframes_with_present_label


# NOTE: Lattice IDs = Label groups
def omezarr_segmentation_annotations_preprocessing(
    internal_segmentation: InternalSegmentation,
):
    ome_zarr_root = open_zarr_structure_from_path(internal_segmentation.input_path)
    root = open_zarr_structure_from_path(
        internal_segmentation.intermediate_zarr_structure_path
    )
    d: AnnotationsMetadata = root.attrs["annotations_dict"]

    assert "labels" in ome_zarr_root, "No label group is present in input OME ZARR"
    for label_gr_name, label_gr in ome_zarr_root.labels.groups():
        labels_metadata_list = label_gr.attrs["image-label"]["colors"]
        # support multiple lattices

        for ind_label_meta in labels_metadata_list:
            # int to put to grid
            label_value = int(ind_label_meta["label-value"])
            ind_label_color_rgba = ind_label_meta["rgba"]
            # color
            ind_label_color_fractional = [i / 255 for i in ind_label_color_rgba]

            # need to create two things: description and segment annotation
            # create description
            description_id = str(uuid4())
            target_id: TargetId = {
                "segment_id": label_value,
                "segmentation_id": str(label_gr_name),
            }

            our_label_gr = root[LATTICE_SEGMENTATION_DATA_GROUPNAME][label_gr_name]
            time = _get_label_time(label_value=label_value, our_label_gr=our_label_gr)
            description: DescriptionData = {
                "id": description_id,
                "target_kind": "lattice",
                "details": None,
                "is_hidden": None,
                "metadata": None,
                "time": time,
                "name": f"segment {label_value}",
                "external_references": [],
                "target_id": target_id,
            }

            segment_annotation: SegmentAnnotationData = {
                "id": str(uuid4()),
                "color": ind_label_color_fractional,
                "segmentation_id": str(label_gr_name),
                "segment_id": label_value,
                "segment_kind": "lattice",
                "time": time,
            }
            d["descriptions"][description_id] = description
            d["segment_annotations"].append(segment_annotation)

    root.attrs["annotations_dict"] = d
    return d
