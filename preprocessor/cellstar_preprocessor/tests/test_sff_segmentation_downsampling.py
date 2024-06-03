import numcodecs
import numpy as np
import pytest
import zarr
from cellstar_preprocessor.flows.common import open_zarr_structure_from_path
from cellstar_preprocessor.flows.constants import (
    LATTICE_SEGMENTATION_DATA_GROUPNAME,
    MESH_SEGMENTATION_DATA_GROUPNAME,
)
from cellstar_preprocessor.flows.segmentation.helper_methods import (
    open_hdf5_as_segmentation_object,
)
from cellstar_preprocessor.flows.segmentation.segmentation_downsampling import (
    sff_segmentation_downsampling,
)
from cellstar_preprocessor.flows.segmentation.sff_preprocessing import sff_preprocessing
from cellstar_preprocessor.model.input import SegmentationPrimaryDescriptor
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
def test_sff_segmentation_downsampling(test_input: TestInput):
    with context_for_tests(test_input, WORKING_FOLDER_FOR_TESTS) as ctx:
        ctx: TestContext
    internal_segmentation = get_sff_internal_segmentation(
        test_input, ctx.test_file_path, ctx.intermediate_zarr_structure_path
    )
    if internal_segmentation == INTERNAL_SEGMENTATION_FOR_TESTING:
        # initialize_intermediate_zarr_structure_for_tests()
        internal_segmentation = INTERNAL_SEGMENTATION_FOR_TESTING
        internal_segmentation.primary_descriptor = (
            SegmentationPrimaryDescriptor.three_d_volume
        )

        zarr_structure: zarr.Group = open_zarr_structure_from_path(
            internal_segmentation.intermediate_zarr_structure_path
        )

        segment_ids_data = np.arange(64).reshape(4, 4, 4)
        # create arr
        grid_arr = zarr_structure.create_dataset(
            f"{LATTICE_SEGMENTATION_DATA_GROUPNAME}/0/1/0/grid", data=segment_ids_data
        )

        set_table = zarr_structure.create_dataset(
            name=f"{LATTICE_SEGMENTATION_DATA_GROUPNAME}/0/1/0/set_table",
            dtype=object,
            object_codec=numcodecs.JSON(),
            shape=1,
        )

        d = {}
        for value in np.unique(segment_ids_data):
            d[str(value)] = [int(value)]

        set_table[...] = [d]

        value_to_segment_id_dict = {"0": {}}
        for value in np.unique(segment_ids_data):
            value_to_segment_id_dict["0"][int(value)] = int(value)

        internal_segmentation.value_to_segment_id_dict = value_to_segment_id_dict

        sff_segmentation_downsampling(internal_segmentation=internal_segmentation)

        # compare grid arrays
        assert (
            zarr_structure[f"{LATTICE_SEGMENTATION_DATA_GROUPNAME}/0/2/0"].grid[...]
            == np.array([[[64, 65], [66, 67]], [[68, 69], [70, 42]]])
        ).all()

        # get set_table
        # update it with
        new_ids = {
            "64": [0, 1, 4, 5, 16, 17, 20, 21],
            "65": [2, 18, 6, 22],
            "66": [8, 9, 24, 25],
            "67": [10, 26],
            "68": [32, 33, 36, 37],
            "69": [34, 38],
            "70": [40, 41],
        }
        updated_dict = (
            zarr_structure[f"{LATTICE_SEGMENTATION_DATA_GROUPNAME}/0/1/0"].set_table[
                ...
            ][0]
            | new_ids
        )
        assert (
            zarr_structure[f"{LATTICE_SEGMENTATION_DATA_GROUPNAME}/0/2/0"].set_table[
                ...
            ][0]
            == updated_dict
        )

    elif internal_segmentation == INTERNAL_MESH_SEGMENTATION_FOR_TESTING:
        # initialize_intermediate_zarr_structure_for_tests()

        sff_segm_obj = open_hdf5_as_segmentation_object(
            internal_segmentation.segmentation_input_path
        )

        sff_preprocessing(internal_segmentation=internal_segmentation)

        # check if zarr structure has right format
        zarr_structure = open_zarr_structure_from_path(
            internal_segmentation.intermediate_zarr_structure_path
        )

        # TODO: do downsampling
        sff_segmentation_downsampling(internal_segmentation=internal_segmentation)

        # TODO: do something like:

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
            # many detail lvl groups
            assert len(segment_gr) > 1
            assert 1 in segment_gr
            # detail_lvl_gr = segment_gr[1]
            print(
                f"There are {len(segment_gr)} detail lvl groups for segment {segment_id}"
            )
            for detail_lvl, detail_lvl_gr in segment_gr.groups():
                for mesh_id, mesh_gr in detail_lvl_gr.groups():
                    assert "triangles" in mesh_gr
                    assert "vertices" in mesh_gr
                    # if there are no more groups
                    assert len(sorted(mesh_gr.group_keys())) == 0
