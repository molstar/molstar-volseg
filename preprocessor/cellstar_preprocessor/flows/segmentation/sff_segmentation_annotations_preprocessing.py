from uuid import uuid4

from cellstar_db.models import (
    AnnotationsMetadata,
    DescriptionData,
    EntryId,
    ExternalReference,
    SegmentAnnotationData,
    TargetId,
)
from cellstar_preprocessor.flows.common import open_zarr_structure_from_path
from cellstar_preprocessor.flows.constants import (
    LATTICE_SEGMENTATION_DATA_GROUPNAME,
    MESH_SEGMENTATION_DATA_GROUPNAME,
)
from cellstar_preprocessor.model.input import SegmentationPrimaryDescriptor
from cellstar_preprocessor.model.segmentation import InternalSegmentation


def _preprocess_external_references(raw_external_references: list[ExternalReference]):
    """Converts ref ids to strings"""
    external_referneces: list[ExternalReference] = []
    for x in raw_external_references:
        r: ExternalReference = {
            "accession": x["accession"],
            "description": x["description"],
            "id": str(x["id"]),
            "label": x["label"],
            "resource": x["resource"],
            "url": x["url"],
        }
        external_referneces.append(r)
    return external_referneces


def sff_segmentation_annotations_preprocessing(
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
    d["details"] = internal_segmentation.raw_sff_annotations["details"]
    d["name"] = internal_segmentation.raw_sff_annotations["name"]

    # NOTE: no volume channel annotations (no color, no labels)
    root = open_zarr_structure_from_path(
        internal_segmentation.intermediate_zarr_structure_path
    )

    time = 0
    if (
        internal_segmentation.primary_descriptor
        == SegmentationPrimaryDescriptor.three_d_volume
    ):
        for lattice_id, lattice_gr in root[
            LATTICE_SEGMENTATION_DATA_GROUPNAME
        ].groups():
            for segment in internal_segmentation.raw_sff_annotations["segment_list"]:
                if str(segment["three_d_volume"]["lattice_id"]) == str(lattice_id):
                    # create description
                    description_id = str(uuid4())
                    target_id: TargetId = {
                        "segment_id": segment["id"],
                        "segmentation_id": str(lattice_id),
                    }
                    raw_external_references: list[ExternalReference] = segment[
                        "biological_annotation"
                    ]["external_references"]
                    external_referneces: list[ExternalReference] = (
                        _preprocess_external_references(raw_external_references)
                    )

                    description: DescriptionData = {
                        "id": description_id,
                        "target_kind": "lattice",
                        "details": None,
                        "is_hidden": None,
                        "metadata": None,
                        "time": time,
                        "name": segment["biological_annotation"]["name"],
                        # for each external reference, make id a string
                        "external_references": external_referneces,
                        "target_id": target_id,
                    }
                    # create segment annotation
                    segment_annotation: SegmentAnnotationData = {
                        "id": str(uuid4()),
                        "color": segment["colour"],
                        "segmentation_id": str(lattice_id),
                        "segment_id": segment["id"],
                        "segment_kind": "lattice",
                        "time": time,
                    }
                    d["descriptions"][description_id] = description
                    d["segment_annotations"].append(segment_annotation)

    elif (
        internal_segmentation.primary_descriptor
        == SegmentationPrimaryDescriptor.mesh_list
    ):
        for set_id, set_gr in root[MESH_SEGMENTATION_DATA_GROUPNAME].groups():
            for segment in internal_segmentation.raw_sff_annotations["segment_list"]:
                description_id = str(uuid4())
                target_id: TargetId = {
                    "segment_id": segment["id"],
                    "segmentation_id": str(set_id),
                }
                raw_external_references: list[ExternalReference] = segment[
                    "biological_annotation"
                ]["external_references"]
                external_referneces: list[ExternalReference] = (
                    _preprocess_external_references(raw_external_references)
                )
                description: DescriptionData = {
                    "id": description_id,
                    "target_kind": "mesh",
                    "details": None,
                    "is_hidden": None,
                    "metadata": None,
                    "time": time,
                    "name": segment["biological_annotation"]["name"],
                    "external_references": external_referneces,
                    "target_id": target_id,
                }
                segment_annotation: SegmentAnnotationData = {
                    "id": str(uuid4()),
                    "color": segment["colour"],
                    "segmentation_id": str(set_id),
                    "segment_id": segment["id"],
                    "segment_kind": "mesh",
                    "time": time,
                }
                d["descriptions"][description_id] = description
                d["segment_annotations"].append(segment_annotation)

    root.attrs["annotations_dict"] = d
    print("Annotations extracted")
    return d
