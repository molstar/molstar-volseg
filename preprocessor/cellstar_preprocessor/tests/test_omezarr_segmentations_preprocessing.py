from cellstar_db.models import AxisName
import pytest
import zarr
from cellstar_preprocessor.flows.constants import LATTICE_SEGMENTATION_DATA_GROUPNAME
from cellstar_preprocessor.flows.segmentation.omezarr_segmentations_preprocessing import (
    omezarr_segmentations_preprocessing,
)
from cellstar_preprocessor.flows.zarr_methods import open_zarr
from cellstar_preprocessor.tests.helper_methods import get_omezarr_internal_segmentation
from cellstar_preprocessor.tests.input_for_tests import (
    OMEZARR_TEST_INPUTS,
    WORKING_FOLDER_FOR_TESTS,
    TestInput,
)
from cellstar_preprocessor.tests.test_context import TestContext, context_for_tests


@pytest.mark.parametrize("omezar_test_input", OMEZARR_TEST_INPUTS)
def test_ome_zarr_labels_preprocessing(omezar_test_input: TestInput):
    with context_for_tests(omezar_test_input, WORKING_FOLDER_FOR_TESTS) as ctx:
        ctx: TestContext
        s = get_omezarr_internal_segmentation(
            omezar_test_input, ctx.test_file_path, ctx.intermediate_zarr_structure_path
        )

        omezarr_segmentations_preprocessing(s=s)
        w = s.get_omezarr_wrapper()
        root = s.get_zarr_root()
        
        assert LATTICE_SEGMENTATION_DATA_GROUPNAME in root
        segmentation_gr = s.get_label_group()
        assert isinstance(segmentation_gr, zarr.Group)
        # check if number of label groups is the same as number of groups in ome zarr
        assert len(segmentation_gr) == len(w.get_labels_group_names())

        for label_gr_name, label_gr in w.get_labels():
            axes = w.get_multiscale().axes

            for arr_resolution, arr in label_gr.arrays():
                segm_3d_arr_shape = arr[...].swapaxes(-3, -1).shape[-3:]
                # i8 is not supported by CIFTools
                if arr.dtype == "i8":
                    segm_3d_arr_dtype = "i4"
                else:
                    segm_3d_arr_dtype = arr.dtype

                assert str(arr_resolution) in segmentation_gr[label_gr_name]
                assert isinstance(
                    segmentation_gr[label_gr_name][arr_resolution], zarr.Group
                )

                # check number of time groups
                if len(axes) == 5 and axes[0]["name"] == "t":
                    n_of_time_groups = arr.shape[0]
                elif len(axes) == 4 and axes[0]["name"] == "c":
                    n_of_time_groups = 1
                else:
                    raise Exception("Axes number/order is not supported")
                
                original_resolution = w.get_multiscale().datasets[
                    0
                ].path

                if len(axes) == 5 and axes[0].name == AxisName.t:
                    image_time_dimension = w.get_zarr_root()[original_resolution].shape[0]
                elif len(axes) == 4 and axes[0].name == AxisName.c:
                    image_time_dimension = 1
                else:
                    raise Exception('Axes length is not supported')

                label_time_dimension = arr.shape[0]

                wrong_time_dimension = False
                if label_time_dimension < image_time_dimension:
                    print(
                        f"Time dimension of label {label_time_dimension} is lower than time dimension of image {image_time_dimension}"
                    )
                    print(
                        "Label data is artificially expanded to time dimension of image using the data of the first label timeframe"
                    )
                    time_dimension = image_time_dimension
                    wrong_time_dimension = True

                if not wrong_time_dimension:
                    assert (
                        len(segmentation_gr[label_gr_name][arr_resolution])
                        == n_of_time_groups
                    )
                else:
                    assert (
                        len(segmentation_gr[label_gr_name][arr_resolution])
                        == time_dimension
                    )

                # for each time group, check if number of channels == -4 dimension of arr
                for time in range(n_of_time_groups):
                    n_of_channel_groups = arr.shape[-4]
                    assert (
                        n_of_channel_groups == 1
                    ), "NGFFs with labels having more than one channel are not supported"

                    assert isinstance(
                        segmentation_gr[label_gr_name][arr_resolution][time], zarr.Group
                    )
                    assert (
                        "grid" in segmentation_gr[label_gr_name][arr_resolution][time]
                    )
                    assert (
                        segmentation_gr[label_gr_name][arr_resolution][time].grid.shape
                        == segm_3d_arr_shape
                    )
                    assert (
                        segmentation_gr[label_gr_name][arr_resolution][time].grid.dtype
                        == segm_3d_arr_dtype
                    )

                    assert (
                        "set_table"
                        in segmentation_gr[label_gr_name][arr_resolution][time]
                    )
                    assert segmentation_gr[label_gr_name][arr_resolution][
                        time
                    ].set_table.shape == (1,)
