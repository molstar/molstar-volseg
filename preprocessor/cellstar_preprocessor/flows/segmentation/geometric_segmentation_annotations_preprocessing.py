from uuid import uuid4

from cellstar_db.models import (
    AnnotationsMetadata,
    DescriptionData,
    EntryId,
    GeometricSegmentationData,
    GeometricSegmentationInputData,
    SegmentAnnotationData,
    SegmentationKind,
    ShapePrimitiveInputData,
    TargetId,
)
from cellstar_preprocessor.flows.zarr_methods import open_zarr
from cellstar_preprocessor.flows.constants import (
    GEOMETRIC_SEGMENTATIONS_ZATTRS,
    RAW_GEOMETRIC_SEGMENTATION_INPUT_ZATTRS,
)
from cellstar_preprocessor.model.segmentation import InternalSegmentation


def geometric_segmentation_annotations_preprocessing(
    s: InternalSegmentation,
):
    a = s.get_annotations()
    
    a.entry_id = EntryId(
        source_db_id=s.entry_data.source_db_id,
        source_db_name=s.entry_data.source_db_name,
    )

    # segmentation is in zattrs
    geometric_segmentation_data = s.get_geometric_segmentation_data()
    # it is a list of objects each of which has timeframes as keys
    for gs in geometric_segmentation_data:
        segmentation_id = gs.segmentation_id

        # collect color from input data as well
        raw = s.get_raw_geometric_segmentation_input_data()[segmentation_id]
        
        primitives = gs.primitives
        # iterate over timeframe index and ShapePrimitiveData
        for timeframe_index, shape_primitive_data in primitives.items():
            # iterate over individual primitives
            time = int(timeframe_index)
            for sp in shape_primitive_data.shape_primitive_list:
                # create description
                description_id = str(uuid4())
                target_id = TargetId(
                    segment_id=sp.id,
                    segmentation_id=segmentation_id,
                )
                description=DescriptionData(
                    id=description_id,
                    target_kind=SegmentationKind.primitve,
                    details=None,
                    is_hidden=None,
                    metadata=None,
                    time=time,
                    name=sp.id,
                    external_references=None,
                    target_id=target_id,
                )
                # get segment annotations

                # how to get color from raw_input_data
                # need to get raw input data for that shape primitive input
                # raw input data should be dict
                # with keys as set ids
                sp_input_list = raw.shape_primitives_input[time]
                filter_results: list[ShapePrimitiveInputData] = list(
                    filter(lambda s: s.parameters.id == sp.id, sp_input_list)
                )
                assert len(filter_results) == 1
                item: ShapePrimitiveInputData = filter_results[0]
                color = item.parameters.color

                segment_annotation=SegmentAnnotationData(
                    id=str(uuid4()),
                    color=color,
                    segmentation_id=segmentation_id,
                    segment_id=sp["id"],
                    segment_kind=SegmentationKind.primitve,
                    time=time,
                )

                a.descriptions[description_id] = description
                a.segment_annotations.append(segment_annotation)

    s.set_annotations(a)
    print("Annotations extracted")
    return a