from cellstar_preprocessor.flows.omezarr import OMEZarrWrapper
import pytest
from cellstar_db.models import AnnotationsMetadata, VolumeChannelAnnotation
from cellstar_preprocessor.flows.segmentation.omezarr_segmentations_preprocessing import (
    omezarr_segmentations_preprocessing,
)
from cellstar_preprocessor.flows.volume.omezarr_volume_annotations_preprocessing import (
    omezarr_volume_annotations_preprocessing,
)
from cellstar_preprocessor.flows.zarr_methods import open_zarr
from cellstar_preprocessor.model.common import hex_to_rgba_normalized
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

        v = get_internal_volume_from_input(
            omezar_test_input, ctx.test_file_path, ctx.intermediate_zarr_structure_path
        )
        internal_segmentation = get_omezarr_internal_segmentation(
            omezar_test_input, ctx.test_file_path, ctx.intermediate_zarr_structure_path
        )

        omezarr_segmentations_preprocessing(s=internal_segmentation)
        d: AnnotationsMetadata = omezarr_volume_annotations_preprocessing(
            v=v
        )
        # d = omezarr

        # root = open_zarr_structure_from_path(
        #     internal_volume.intermediate_zarr_structure_path
        # )

        # d = root.attrs.annotations_dict"]
        assert d.entry_id.source_db_id == v.entry_data.source_db_id
        assert d.entry_id.source_db_name == v.entry_data.source_db_name

        list(d.descriptions.items())

        w = v.get_omezarr_wrapper()
        omero_channels = w.get_root_zattrs_wrapper().omero.channels
        for c in omero_channels:
            assert list(
                filter(
                    lambda v: v.channel_id == str(c.label),
                    d.volume_channels_annotations,
                )
            )[0]
            vol_ch_annotation: VolumeChannelAnnotation = list(
                filter(
                    lambda v: v.channel_id == str(c.label),
                    d.volume_channels_annotations,
                )
            )[0]

            assert vol_ch_annotation.color == hex_to_rgba_normalized(c.color)
            assert vol_ch_annotation.label == c.label
