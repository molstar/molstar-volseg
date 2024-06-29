from cellstar_preprocessor.flows.segmentation.omezarr_segmentation_annotations_preprocessing import omezarr_segmentation_annotations_preprocessing
from cellstar_preprocessor.flows.zarr_methods import open_zarr
import pytest
from cellstar_db.models import (
    AnnotationsMetadata,
    SegmentationKind,
    VolumeChannelAnnotation,
    DescriptionData,
    SegmentAnnotationData,
)
from cellstar_preprocessor.flows.common import (
    hex_to_rgba_normalized,
)
from cellstar_preprocessor.flows.segmentation.omezarr_segmentations_preprocessing import (
    omezarr_segmentations_preprocessing,
)
from cellstar_preprocessor.flows.volume.omezarr_volume_annotations_preprocessing import (
    omezarr_volume_annotations_preprocessing,
)
from cellstar_preprocessor.tests.helper_methods import (
    get_internal_volume_from_input,
    get_omezarr_internal_segmentation,
)
from cellstar_preprocessor.tests.input_for_tests import (
    OMEZARR_TEST_INPUTS,
    WORKING_FOLDER_FOR_TESTS,
    TestInput,
)
from cellstar_preprocessor.tests.test_context import TestContext, context_for_tests


@pytest.mark.parametrize("omezar_test_input", OMEZARR_TEST_INPUTS)
def test_omezarr_segmentation_annotations_preprocessing(omezar_test_input: TestInput):
    with context_for_tests(omezar_test_input, WORKING_FOLDER_FOR_TESTS) as ctx:
        ctx: TestContext
        internal_segmentation = get_omezarr_internal_segmentation(
            omezar_test_input, ctx.test_file_path, ctx.intermediate_zarr_structure_path
        )

        omezarr_segmentations_preprocessing(internal_segmentation=internal_segmentation)
        d: AnnotationsMetadata = omezarr_segmentation_annotations_preprocessing(
            s=internal_segmentation
        )
        # d = omezarr

        ome_zarr_root = open_zarr(internal_segmentation.input_path)
        ome_zarr_attrs = ome_zarr_root.attrs

        # root = open_zarr_structure_from_path(
        #     internal_volume.intermediate_zarr_structure_path
        # )

        # d = root.attrs.annotations_dict"]
        assert d.entry_id.source_db_id == internal_segmentation.entry_data.source_db_id
        assert (
            d.entry_id.source_db_name == internal_segmentation.entry_data.source_db_name
        )

        description_items = list(d.descriptions.items())    
        assert "labels" in ome_zarr_root, "No labels group"
        
        for label_gr_name, label_gr in ome_zarr_root.labels.groups():
            # PLAN
            # for each label gr
            # check if for each

            # # check if there is object in d["segmentation_lattices"] with that lattice_id == label_gr_name
            # assert list(filter(lambda lat: lat["lattice_id"] == label_gr_name, d["segmentation_lattices"]))[0]
            # lat_obj = list(filter(lambda lat: lat["lattice_id"] == label_gr_name, d["segmentation_lattices"]))[0]

            labels_metadata_list = label_gr.attrs["image-label"]["colors"]
            for ind_label_meta in labels_metadata_list:
                label_value = int(ind_label_meta["label-value"])
                ind_label_color_rgba = ind_label_meta["rgba"]
                ind_label_color_fractional = [i / 255 for i in ind_label_color_rgba]

                # find description
                description_filter_results = list(
                    filter(
                        lambda d: d[1].target_id.segment_id == label_value
                        and d[1].target_id.segmentation_id == label_gr_name,
                        description_items,
                    )
                )
                assert len(description_filter_results) == 1
                description_item: DescriptionData = description_filter_results[0][1]

                # check that
                assert description_item.target_id.segment_id == label_value
                assert (
                    description_item.target_id.segmentation_id
                    == label_gr_name
                )
                assert description_item.target_kind == "lattice"

                # find segment annotation
                segment_annotations: list[SegmentAnnotationData] = d.segment_annotations
                segment_annotation_filter_results = list(
                    filter(
                        lambda a: a.segment_id == label_value
                        and a.segment_kind == SegmentationKind.lattice
                        and a.segmentation_id == label_gr_name,
                        segment_annotations,
                    )
                )
                assert len(segment_annotation_filter_results) == 1
                segment_annotation_item: SegmentAnnotationData = (
                    segment_annotation_filter_results[0]
                )

                # check each field
                assert (
                    segment_annotation_item.color == ind_label_color_fractional
                )
                assert segment_annotation_item.segment_id == label_value
                assert segment_annotation_item.segment_kind == SegmentationKind.lattice
                # can be not 0
                # assert segment_annotation_item['time'] == 0
