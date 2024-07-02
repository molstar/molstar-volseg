from typing import Any

import pytest
from cellstar_db.models import (
    DescriptionData,
    ExternalReference,
    SegmentAnnotationData,
    SegmentationKind,
    SegmentationPrimaryDescriptor,
)
from cellstar_preprocessor.flows.segmentation.helper_methods import (
    extract_raw_annotations_from_sff,
)
from cellstar_preprocessor.flows.segmentation.sff_segmentation_annotations_preprocessing import (
    _preprocess_raw_external_references,
    sff_segmentation_annotations_preprocessing,
)
from cellstar_preprocessor.flows.segmentation.sff_segmentation_preprocessing import (
    sff_segmentation_preprocessing,
)
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
        sff_segmentation_preprocessing(internal_segmentation=internal_segmentation)
        d = sff_segmentation_annotations_preprocessing(
            internal_segmentation=internal_segmentation
        )

        r = extract_raw_annotations_from_sff(internal_segmentation.input_path)
        assert d.details == r["details"]
        assert d.name == r["name"]
        assert d.entry_id.source_db_id == internal_segmentation.entry_data.source_db_id
        assert (
            d.entry_id.source_db_name == internal_segmentation.entry_data.source_db_name
        )

        description_items = list(d.descriptions.items())
        for segment in r["segment_list"]:
            # TODO: unify
            if (
                internal_segmentation.primary_descriptor
                == SegmentationPrimaryDescriptor.three_d_volume
            ):
                segmentation_id = str(segment["three_d_volume"]["lattice_id"])
                kind = SegmentationKind.lattice
            else:
                assert (
                    internal_segmentation.primary_descriptor
                    == SegmentationPrimaryDescriptor.mesh_list
                ), "Primary descriptor not supported"
                segmentation_id = "0"
                kind = SegmentationKind.mesh

                description_filter_results = list(
                    filter(
                        lambda d: d[1].target_id.segment_id == segment["id"]
                        and d[1].target_id.segmentation_id == segmentation_id,
                        description_items,
                    )
                )
                assert len(description_filter_results) == 1
                description_item: DescriptionData = description_filter_results[0][1]

                raw_external_references: dict[str, Any] = segment[
                    "biological_annotation"
                ]["external_references"]
                external_referneces: list[ExternalReference] = (
                    _preprocess_raw_external_references(raw_external_references)
                )

                assert description_item.external_references == external_referneces
                assert description_item.name == segment["biological_annotation"]["name"]

                assert description_item.target_kind == kind

                segment_annotations: list[SegmentAnnotationData] = d.segment_annotations
                segment_annotation_filter_results = list(
                    filter(
                        lambda a: a.segment_id == segment["id"]
                        and a.segment_kind == kind
                        and a.segmentation_id == segmentation_id,
                        segment_annotations,
                    )
                )
                assert len(segment_annotation_filter_results) == 1
                segment_annotation_item: SegmentAnnotationData = (
                    segment_annotation_filter_results[0]
                )

                # check each field
                assert segment_annotation_item.color == list(segment["colour"])
                assert segment_annotation_item.segment_id == segment["id"]
                assert segment_annotation_item.segment_kind == kind
                assert segment_annotation_item.time == 0

            # elif (
            #     internal_segmentation.primary_descriptor
            #     == SegmentationPrimaryDescriptor.mesh_list
            # ):
            #     # NOTE: only single set for meshes
            #     set_id = "0"

            #     description_filter_results = list(
            #         filter(
            #             lambda d: d[1].target_id.segment_id == segment["id"]
            #             and d[1].target_id.segmentation_id == set_id,
            #             description_items,
            #         )
            #     )

            #     assert len(description_filter_results) == 1
            #     description_item: DescriptionData = description_filter_results[0][1]

            #     raw_external_references: dict[str, Any] = segment[
            #         "biological_annotation"
            #     ]["external_references"]
            #     external_referneces: list[ExternalReference] = (
            #         _preprocess_raw_external_references(raw_external_references)
            #     )

            #     assert description_item.external_references == external_referneces
            #     assert (
            #         description_item.name == segment["biological_annotation"]["name"]
            #     )

            #     assert description_item.target_kind == SegmentationKind.mesh

            #     segment_annotations: list[SegmentAnnotationData] = d.segment_annotations
            #     segment_annotation_filter_results = list(
            #         filter(
            #             lambda a: a.segment_id == segment["id"]
            #             and a.segment_kind == SegmentationKind.mesh
            #             and a.segmentation_id == set_id,
            #             segment_annotations,
            #         )
            #     )
            #     assert len(segment_annotation_filter_results) == 1
            #     segment_annotation_item: SegmentAnnotationData = (
            #         segment_annotation_filter_results[0]
            #     )

            #     # check each field
            #     assert segment_annotation_item["color"] == segment["colour"]
            #     assert segment_annotation_item["segment_id"] == segment["id"]
            #     assert segment_annotation_item["segment_kind"] == "mesh"
            #     assert segment_annotation_item["time"] == 0
