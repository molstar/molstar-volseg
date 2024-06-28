from uuid import uuid4

from cellstar_db.models import (
    AnnotationsMetadata,
    DescriptionData,
    EntryId,
    GeometricSegmentationData,
    GeometricSegmentationInputData,
    SegmentAnnotationData,
    ShapePrimitiveInputData,
    TargetId,
)
from cellstar_preprocessor.flows.common import open_zarr_structure_from_path
from cellstar_preprocessor.flows.constants import (
    GEOMETRIC_SEGMENTATIONS_ZATTRS,
    RAW_GEOMETRIC_SEGMENTATION_INPUT_ZATTRS,
)
from cellstar_preprocessor.model.segmentation import InternalSegmentation


def geometric_segmentation_annotations_preprocessing(
    internal_segmentation: InternalSegmentation,
):
    root = open_zarr_structure_from_path(
        internal_segmentation.intermediate_zarr_structure_path
    )
    d: AnnotationsMetadata = root.attrs["annotations_dict"]

    d["entry_id"] = EntryId(
        source_db_id=internal_segmentation.entry_data.source_db_id,
        source_db_name=internal_segmentation.entry_data.source_db_name,
    )

    # NOTE: no volume channel annotations (no color, no labels)
    root = open_zarr_structure_from_path(
        internal_segmentation.intermediate_zarr_structure_path
    )

    # segmentation is in zattrs
    geometric_segmentation_data: list[GeometricSegmentationData] = root.attrs[
        GEOMETRIC_SEGMENTATIONS_ZATTRS
    ]
    # it is a list of objects each of which has timeframes as keys
    for gs_set in geometric_segmentation_data:
        set_id = gs_set["segmentation_id"]

        # collect color from input data as well
        raw_input_data = root.attrs[RAW_GEOMETRIC_SEGMENTATION_INPUT_ZATTRS][set_id]
        input_data = GeometricSegmentationInputData(**raw_input_data)

        primitives = gs_set["primitives"]
        # iterate over timeframe index and ShapePrimitiveData
        for timeframe_index, shape_primitive_data in primitives.items():
            # iterate over individual primitives
            time = int(timeframe_index)
            for sp in shape_primitive_data["shape_primitive_list"]:
                # create description
                description_id = str(uuid4())
                target_id: TargetId = {
                    "segment_id": sp["id"],
                    "segmentation_id": set_id,
                }
                description: DescriptionData = {
                    "id": description_id,
                    "target_kind": "primitive",
                    "details": None,
                    "is_hidden": None,
                    "metadata": None,
                    "time": time,
                    "name": sp["id"],
                    "external_references": None,
                    "target_id": target_id,
                }
                # get segment annotations

                # how to get color from raw_input_data
                # need to get raw input data for that shape primitive input
                # raw input data should be dict
                # with keys as set ids
                sp_input_list = input_data.shape_primitives_input[time]
                filter_results: list[ShapePrimitiveInputData] = list(
                    filter(lambda s: s.parameters.id == sp["id"], sp_input_list)
                )
                assert len(filter_results) == 1
                item: ShapePrimitiveInputData = filter_results[0]
                color = item.parameters.color

                segment_annotation: SegmentAnnotationData = {
                    "id": str(uuid4()),
                    "color": color,
                    "segmentation_id": set_id,
                    "segment_id": sp["id"],
                    "segment_kind": "primitive",
                    "time": time,
                }

                d["descriptions"][description_id] = description
                d["segment_annotations"].append(segment_annotation)

    root.attrs["annotations_dict"] = d
    print("Annotations extracted")
    return d
