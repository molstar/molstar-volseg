from uuid import uuid4

import zarr
import zarr.storage
from cellstar_db.models import (
    DescriptionData,
    EntryId,
    SegmentAnnotationData,
    SegmentationKind,
    TargetId,
)
from cellstar_preprocessor.model.segmentation import InternalSegmentation


def _get_label_time(label_value: int, lattice_gr: zarr.Group):
    timeframes_with_present_label: list[int] = []
    # PLAN:
    # take first available resolution
    available_resolutions = sorted(lattice_gr.group_keys())
    first_resolution = available_resolutions[0]
    # loop over timeframes
    first_resolution_gr = lattice_gr[first_resolution]
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
    s: InternalSegmentation,
):
    # TODO: use wrapper here
    w = s.get_omezarr_wrapper()
    a = s.get_annotations()
    s.set_entry_id_in_annotations()
    for label_gr_name in w.get_label_names():
        label_zattrs = w.get_label_zattrs(label_gr_name)
        colors_meta = label_zattrs.image_label.colors

        for c in colors_meta:
            color = [i / 255 for i in c.rgba]
            label_value = int(c.label_value)
            description_id = str(uuid4())
            target_id = TargetId(
                segment_id=label_value,
                segmentation_id=str(label_gr_name),
            )

            lattice_gr: zarr.Group = s.get_segmentation_data_group(
                SegmentationKind.lattice
            )[label_gr_name]
            time = _get_label_time(label_value=label_value, lattice_gr=lattice_gr)
            description = DescriptionData(
                id=description_id,
                target_kind=SegmentationKind.lattice,
                details=None,
                is_hidden=None,
                metadata=None,
                time=time,
                name=f"segment {label_value}",
                external_references=[],
                target_id=target_id,
            )
            segment_annotation = SegmentAnnotationData(
                id=str(uuid4()),
                color=color,
                segmentation_id=str(label_gr_name),
                segment_id=label_value,
                segment_kind=SegmentationKind.lattice,
                time=time,
            )
            a.descriptions[description_id] = description
            a.segment_annotations.append(segment_annotation)

    s.set_annotations(a)
    return a
