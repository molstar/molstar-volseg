from uuid import uuid4

import zarr
import zarr.storage
from cellstar_db.models import (
    AnnotationsMetadata,
    DescriptionData,
    EntryId,
    SegmentAnnotationData,
    TargetId,
)
from cellstar_preprocessor.flows.common import (
    get_channel_annotations,
    open_zarr_structure_from_path,
)
from cellstar_preprocessor.flows.constants import LATTICE_SEGMENTATION_DATA_GROUPNAME
from cellstar_preprocessor.model.volume import InternalVolume


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
def extract_omezarr_annotations(internal_volume: InternalVolume):
    ome_zarr_root = open_zarr_structure_from_path(internal_volume.volume_input_path)
    root = open_zarr_structure_from_path(
        internal_volume.intermediate_zarr_structure_path
    )
    d: AnnotationsMetadata = root.attrs["annotations_dict"]

    d["entry_id"] = EntryId(
        source_db_id=internal_volume.entry_data.source_db_id,
        source_db_name=internal_volume.entry_data.source_db_name,
    )

    d["volume_channels_annotations"] = get_channel_annotations(ome_zarr_root.attrs)

    # TODO: omezarr annotations (image label) should have time
    # NOTE: how to get it?
    # first check if there is time dimension
    #
    # for each label (label_value) check in which timeframe
    # of specific label_gr it is present
    # NOTE: assumes that if label is present in original resolution data
    # for that timeframe, it is present in downsamplings

    # time could be a range

    # time = 0
    if "labels" in ome_zarr_root:
        for label_gr_name, label_gr in ome_zarr_root.labels.groups():
            labels_metadata_list = label_gr.attrs["image-label"]["colors"]
            # support multiple lattices

            # for segment in intern.raw_sff_annotations["segment_list"]:
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
                time = _get_label_time(
                    label_value=label_value, our_label_gr=our_label_gr
                )
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
