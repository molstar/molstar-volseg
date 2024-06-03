import pytest
from cellstar_db.models import DescriptionData, ExternalReference, SegmentAnnotationData
from cellstar_preprocessor.flows.segmentation.extract_annotations_from_sff_segmentation import (
    _preprocess_external_references,
    extract_annotations_from_sff_segmentation,
)
from cellstar_preprocessor.flows.segmentation.helper_methods import (
    extract_raw_annotations_from_sff,
)
from cellstar_preprocessor.flows.segmentation.sff_preprocessing import sff_preprocessing
from cellstar_preprocessor.model.input import SegmentationPrimaryDescriptor
from cellstar_preprocessor.tests.helper_methods import get_sff_internal_segmentation
from cellstar_preprocessor.tests.input_for_tests import (
    SFF_TEST_INPUTS,
    WORKING_FOLDER_FOR_TESTS,
    TestInput,
)
from cellstar_preprocessor.tests.test_context import TestContext, context_for_tests


@pytest.mark.parametrize("test_input", SFF_TEST_INPUTS)
def test_extract_annotations_from_sff_segmentation(test_input: TestInput):
    with context_for_tests(test_input, WORKING_FOLDER_FOR_TESTS) as ctx:
        ctx: TestContext
        internal_segmentation = get_sff_internal_segmentation(
            test_input, ctx.test_file_path, ctx.intermediate_zarr_structure_path
        )
        sff_preprocessing(internal_segmentation=internal_segmentation)
        d = extract_annotations_from_sff_segmentation(
            internal_segmentation=internal_segmentation
        )

        r = extract_raw_annotations_from_sff(
            internal_segmentation.segmentation_input_path
        )

        assert d["details"] == r["details"]
        assert d["name"] == r["name"]
        assert (
            d["entry_id"]["source_db_id"]
            == internal_segmentation.entry_data.source_db_id
        )
        assert (
            d["entry_id"]["source_db_name"]
            == internal_segmentation.entry_data.source_db_name
        )

        description_items = list(d["descriptions"].items())
        for segment in r["segment_list"]:
            if (
                internal_segmentation.primary_descriptor
                == SegmentationPrimaryDescriptor.three_d_volume
            ):
                lattice_id: str = str(segment["three_d_volume"]["lattice_id"])

                description_filter_results = list(
                    filter(
                        lambda d: d[1]["target_id"]["segment_id"] == segment["id"]
                        and d[1]["target_id"]["segmentation_id"] == lattice_id,
                        description_items,
                    )
                )
                assert len(description_filter_results) == 1
                description_item: DescriptionData = description_filter_results[0][1]

                raw_external_references: list[ExternalReference] = segment[
                    "biological_annotation"
                ]["external_references"]
                external_referneces: list[ExternalReference] = (
                    _preprocess_external_references(raw_external_references)
                )

                assert description_item["external_references"] == external_referneces
                assert (
                    description_item["name"] == segment["biological_annotation"]["name"]
                )

                assert description_item["target_kind"] == "lattice"

                segment_annotations: list[SegmentAnnotationData] = d[
                    "segment_annotations"
                ]
                segment_annotation_filter_results = list(
                    filter(
                        lambda a: a["segment_id"] == segment["id"]
                        and a["segment_kind"] == "lattice"
                        and a["segmentation_id"] == lattice_id,
                        segment_annotations,
                    )
                )
                assert len(segment_annotation_filter_results) == 1
                segment_annotation_item: SegmentAnnotationData = (
                    segment_annotation_filter_results[0]
                )

                # check each field
                assert segment_annotation_item["color"] == segment["colour"]
                assert segment_annotation_item["segment_id"] == segment["id"]
                assert segment_annotation_item["segment_kind"] == "lattice"
                assert segment_annotation_item["time"] == 0

            elif (
                internal_segmentation.primary_descriptor
                == SegmentationPrimaryDescriptor.mesh_list
            ):
                # NOTE: only single set for meshes
                set_id = "0"

                description_filter_results = list(
                    filter(
                        lambda d: d[1]["target_id"]["segment_id"] == segment["id"]
                        and d[1]["target_id"]["segmentation_id"] == set_id,
                        description_items,
                    )
                )

                assert len(description_filter_results) == 1
                description_item: DescriptionData = description_filter_results[0][1]

                raw_external_references: list[ExternalReference] = segment[
                    "biological_annotation"
                ]["external_references"]
                external_referneces: list[ExternalReference] = (
                    _preprocess_external_references(raw_external_references)
                )

                assert description_item["external_references"] == external_referneces
                assert (
                    description_item["name"] == segment["biological_annotation"]["name"]
                )

                assert description_item["target_kind"] == "mesh"

                segment_annotations: list[SegmentAnnotationData] = d[
                    "segment_annotations"
                ]
                segment_annotation_filter_results = list(
                    filter(
                        lambda a: a["segment_id"] == segment["id"]
                        and a["segment_kind"] == "mesh"
                        and a["segmentation_id"] == set_id,
                        segment_annotations,
                    )
                )
                assert len(segment_annotation_filter_results) == 1
                segment_annotation_item: SegmentAnnotationData = (
                    segment_annotation_filter_results[0]
                )

                # check each field
                assert segment_annotation_item["color"] == segment["colour"]
                assert segment_annotation_item["segment_id"] == segment["id"]
                assert segment_annotation_item["segment_kind"] == "mesh"
                assert segment_annotation_item["time"] == 0
