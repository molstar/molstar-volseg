from cellstar_preprocessor.flows.zarr_methods import open_zarr
import pytest
from cellstar_db.models import (
    AnnotationsMetadata,
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
def test_omezarr_volume_annotations_preprocessing(omezar_test_input: TestInput):
    with context_for_tests(omezar_test_input, WORKING_FOLDER_FOR_TESTS) as ctx:
        ctx: TestContext
        # suppose to open context with files and zarr structures
        # then here create internal volumes, segmentations etc.
        # initialize_intermediate_zarr_structure_for_tests()

        internal_volume = get_internal_volume_from_input(
            omezar_test_input, ctx.test_file_path, ctx.intermediate_zarr_structure_path
        )
        internal_segmentation = get_omezarr_internal_segmentation(
            omezar_test_input, ctx.test_file_path, ctx.intermediate_zarr_structure_path
        )

        omezarr_segmentations_preprocessing(internal_segmentation=internal_segmentation)
        d: AnnotationsMetadata = omezarr_volume_annotations_preprocessing(
            v=internal_volume
        )
        # d = omezarr

        ome_zarr_root = open_zarr(internal_volume.input_path)
        ome_zarr_attrs = ome_zarr_root.attrs

        # root = open_zarr_structure_from_path(
        #     internal_volume.intermediate_zarr_structure_path
        # )

        # d = root.attrs.annotations_dict"]
        assert d.entry_id.source_db_id == internal_volume.entry_data.source_db_id
        assert (
            d.entry_id.source_db_name == internal_volume.entry_data.source_db_name
        )

        description_items = list(d.descriptions.items())

        for channel_id, channel in enumerate(ome_zarr_attrs["omero"]["channels"]):
            # PLAN
            # for each channel in omero channels
            # check if in volume channel annotations exist object with that channel_id
            # that its color is equal to channel color
            # that its label is equal to channel label
            assert list(
                filter(
                    lambda v: v.channel_id == str(channel_id),
                    d.volume_channels_annotations,
                )
            )[0]
            vol_ch_annotation: VolumeChannelAnnotation = list(
                filter(
                    lambda v: v.channel_id == str(channel_id),
                    d.volume_channels_annotations,
                )
            )[0]

            assert vol_ch_annotation.color == hex_to_rgba_normalized(
                channel["color"]
            )
            assert vol_ch_annotation.label == channel["label"]