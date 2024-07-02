from typing import Any
from uuid import uuid4

from cellstar_db.models import (
    AnnotationsMetadata,
    DescriptionData,
    EntryId,
    ExternalReference,
    SegmentAnnotationData,
    SegmentationKind,
    SegmentationPrimaryDescriptor,
    TargetId,
)
from cellstar_preprocessor.flows.constants import (
    LATTICE_SEGMENTATION_DATA_GROUPNAME,
    MESH_SEGMENTATION_DATA_GROUPNAME,
)
from cellstar_preprocessor.flows.zarr_methods import open_zarr
from cellstar_preprocessor.model.segmentation import InternalSegmentation


def _preprocess_raw_external_references(raw_external_references: list[dict[str, Any]]):
    """Converts dict to pydantic model and ref ids to strings"""
    external_referneces: list[ExternalReference] = []
    for x in raw_external_references:
        r = ExternalReference(
            id=str(x["id"]),
            resource=x["resource"],
            url=x["url"],
            description=x["description"],
            accession=x["accession"],
            label=x["label"],
        )
        external_referneces.append(r)
    return external_referneces


def __process_raw_segment_data(
    time: int,
    segment: dict[str, Any],
    d: AnnotationsMetadata,
    segmentation_id: str,
    segmentation_kind: SegmentationKind,
):
    description_id = str(uuid4())
    target_id = TargetId(segment_id=segment["id"], segmentation_id=segmentation_id)
    raw_external_references: list[dict[str, Any]] = segment["biological_annotation"][
        "external_references"
    ]
    external_referneces: list[ExternalReference] = _preprocess_raw_external_references(
        raw_external_references
    )

    description = DescriptionData(
        id=description_id,
        target_kind=segmentation_kind,
        details=None,
        is_hidden=None,
        metadata=None,
        time=time,
        name=segment["biological_annotation"]["name"],
        external_references=external_referneces,
        target_id=target_id,
    )
    # create segment annotation
    segment_annotation = SegmentAnnotationData(
        id=str(uuid4()),
        color=segment["colour"],
        segmentation_id=segmentation_id,
        segment_id=segment["id"],
        segment_kind=segmentation_kind,
        time=time,
    )
    d.descriptions[description_id] = description
    d.segment_annotations.append(segment_annotation)
    return d


def _processs_raw_sff_annotations(
    internal_segmentation: InternalSegmentation,
    d: AnnotationsMetadata,
    segmentation_id: str,
):
    time = 0

    for segment in internal_segmentation.raw_sff_annotations["segment_list"]:
        if segment["three_d_volume"] == None:
            d = __process_raw_segment_data(
                time, segment, d, segmentation_id, SegmentationKind.mesh
            )
        else:
            if str(segment["three_d_volume"]["lattice_id"]) == segmentation_id:
                d = __process_raw_segment_data(
                    time, segment, d, segmentation_id, SegmentationKind.lattice
                )

    return d


def sff_segmentation_annotations_preprocessing(
    internal_segmentation: InternalSegmentation,
):
    root = open_zarr(internal_segmentation.path)
    d: AnnotationsMetadata = AnnotationsMetadata.parse_obj(
        root.attrs["annotations_dict"]
    )

    d.entry_id = EntryId(
        source_db_id=internal_segmentation.entry_data.source_db_id,
        source_db_name=internal_segmentation.entry_data.source_db_name,
    )
    d.details = internal_segmentation.raw_sff_annotations["details"]
    d.name = internal_segmentation.raw_sff_annotations["name"]

    # NOTE: no volume channel annotations (no color, no labels)
    root = open_zarr(internal_segmentation.path)

    if (
        internal_segmentation.primary_descriptor
        == SegmentationPrimaryDescriptor.three_d_volume
    ):
        for lattice_id, lattice_gr in root[
            LATTICE_SEGMENTATION_DATA_GROUPNAME
        ].groups():
            d = _processs_raw_sff_annotations(internal_segmentation, d, lattice_id)
    elif (
        internal_segmentation.primary_descriptor
        == SegmentationPrimaryDescriptor.mesh_list
    ):
        for set_id, set_gr in root[MESH_SEGMENTATION_DATA_GROUPNAME].groups():
            d = _processs_raw_sff_annotations(internal_segmentation, d, set_id)
    root.attrs["annotations_dict"] = d.dict()
    print("Annotations extracted")
    return d
