import pytest
import zarr
from cellstar_db.models import SegmentationPrimaryDescriptor
from cellstar_preprocessor.flows.constants import (
    LATTICE_SEGMENTATION_DATA_GROUPNAME,
    MESH_SEGMENTATION_DATA_GROUPNAME,
)
from cellstar_preprocessor.flows.segmentation.helper_methods import (
    open_hdf5_as_segmentation_object,
)
from cellstar_preprocessor.flows.segmentation.sff_segmentation_preprocessing import (
    sff_segmentation_preprocessing,
)
from cellstar_preprocessor.flows.zarr_methods import open_zarr
from cellstar_preprocessor.tests.helper_methods import get_sff_internal_segmentation
from cellstar_preprocessor.tests.input_for_tests import (
    INTERNAL_MESH_SEGMENTATION_FOR_TESTING,
    INTERNAL_SEGMENTATION_FOR_TESTING,
    SFF_TEST_INPUTS,
    WORKING_FOLDER_FOR_TESTS,
    TestInput,
)
from cellstar_preprocessor.tests.test_context import TestContext, context_for_tests

SEGMENTATIONS = [
    INTERNAL_SEGMENTATION_FOR_TESTING,
    INTERNAL_MESH_SEGMENTATION_FOR_TESTING,
]


@pytest.mark.parametrize("test_input", SFF_TEST_INPUTS)
def test_sff_segmentation_preprocessing(test_input: TestInput):
    with context_for_tests(test_input, WORKING_FOLDER_FOR_TESTS) as ctx:
        ctx: TestContext

        internal_segmentation = get_sff_internal_segmentation(
            test_input, ctx.test_file_path, ctx.intermediate_zarr_structure_path
        )
        sff_segm_obj = open_hdf5_as_segmentation_object(
            internal_segmentation.input_path
        )

        sff_segmentation_preprocessing(internal_segmentation=internal_segmentation)

        # check if zarr structure has right format
        zarr_structure = open_zarr(internal_segmentation.path)

        # n of segments

        if (
            internal_segmentation.primary_descriptor
            == SegmentationPrimaryDescriptor.three_d_volume
        ):
            assert LATTICE_SEGMENTATION_DATA_GROUPNAME in zarr_structure
            segmentation_gr = zarr_structure[LATTICE_SEGMENTATION_DATA_GROUPNAME]
            assert isinstance(segmentation_gr, zarr.Group)
            assert len(segmentation_gr) == len(sff_segm_obj.lattice_list)

            for lattice_id, lattice_gr in segmentation_gr.groups():
                # single resolution group
                assert len(lattice_gr) == 1
                assert 1 in lattice_gr
                resolution_gr = lattice_gr[1]
                assert isinstance(resolution_gr, zarr.Group)

                # single time group
                assert len(resolution_gr) == 1
                assert 0 in resolution_gr
                timeframe_gr = resolution_gr[0]
                assert isinstance(timeframe_gr, zarr.Group)

                # grid and set table
                assert len(timeframe_gr) == 2
                assert "grid" in timeframe_gr
                lattice_from_sff = list(
                    filter(
                        lambda lat: str(lat.id) == lattice_id, sff_segm_obj.lattice_list
                    )
                )[0]
                grid_shape = (
                    lattice_from_sff.size.rows,
                    lattice_from_sff.size.cols,
                    lattice_from_sff.size.sections,
                )
                assert timeframe_gr.grid.shape == grid_shape

                assert "set_table" in timeframe_gr
                assert timeframe_gr.set_table.shape == (1,)

        # empiar-10070
        elif (
            internal_segmentation.primary_descriptor
            == SegmentationPrimaryDescriptor.mesh_list
        ):
            assert MESH_SEGMENTATION_DATA_GROUPNAME in zarr_structure
            segmentation_gr = zarr_structure[MESH_SEGMENTATION_DATA_GROUPNAME]
            assert isinstance(segmentation_gr, zarr.Group)

            # order
            # mesh set_id => timeframe => segment_id => detail_lvl => mesh_id in meshlist

            # single set
            assert len(segmentation_gr) == 1
            set_gr = segmentation_gr[0]
            # single timeframe
            assert len(set_gr) == 1
            timeframe_gr = set_gr[0]

            # number of segments
            assert len(timeframe_gr) == len(sff_segm_obj.segment_list)
            for segment_id, segment_gr in timeframe_gr.groups():
                # single detail lvl group - original
                assert len(segment_gr) == 1
                assert 1 in segment_gr
                detail_lvl_gr = segment_gr[1]
                for mesh_id, mesh_gr in detail_lvl_gr.groups():
                    assert "triangles" in mesh_gr
                    assert "vertices" in mesh_gr
                    # if there are no more groups
                    assert len(sorted(mesh_gr.group_keys())) == 0
