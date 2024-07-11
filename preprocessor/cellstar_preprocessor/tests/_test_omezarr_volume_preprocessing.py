import pytest
import zarr
from cellstar_db.models import AxisName
from cellstar_preprocessor.flows.constants import VOLUME_DATA_GROUPNAME
from cellstar_preprocessor.flows.volume.omezarr_volume_preprocessing import (
    omezarr_volume_preprocessing,
)
from cellstar_preprocessor.tests.helper_methods import get_internal_volume_from_input
from cellstar_preprocessor.tests.input_for_tests import (
    OMEZARR_TEST_INPUTS,
    WORKING_FOLDER_FOR_TESTS,
    TestInput,
)
from cellstar_preprocessor.tests.test_context import TestContext, context_for_tests


@pytest.mark.parametrize("omezar_test_input", OMEZARR_TEST_INPUTS)
def test_omezarr_volume_preprocessing(omezar_test_input: TestInput):
    with context_for_tests(omezar_test_input, WORKING_FOLDER_FOR_TESTS) as ctx:
        ctx: TestContext
        v = get_internal_volume_from_input(
            omezar_test_input, ctx.test_input_asset_path, ctx.working_folder
        )

        omezarr_volume_preprocessing(v=v)

        w = v.get_omezarr_wrapper()

        # ome_zarr_root = zarr.open_group(v.input_path)
        # root_zattrs = ome_zarr_root.attrs
        # multiscales = root_zattrs["multiscales"]
        axes = w.get_image_multiscale().axes

        root = v.get_zarr_root()
        assert VOLUME_DATA_GROUPNAME in root
        volume_gr = v.get_volume_data_group()
        assert isinstance(volume_gr, zarr.Group)

        # check if number of resolution groups is the same as number of arrays in ome zarr
        assert len(volume_gr) == len(w.get_image_resolutions())

        for volume_arr_resolution, volume_arr in w.get_image_group().arrays():
            volume_3d_arr_shape = volume_arr[...].swapaxes(-3, -1).shape[-3:]

            assert str(volume_arr_resolution) in volume_gr
            assert isinstance(volume_gr[volume_arr_resolution], zarr.Group)

            # check number of time groups
            if len(axes) == 5 and axes[0].name == AxisName.t:
                n_of_time_groups = volume_arr.shape[0]
            elif len(axes) == 4 and axes[0].name == AxisName.c:
                n_of_time_groups = 1
            else:
                raise Exception("Axes number/order is not supported")

            assert len(volume_gr[volume_arr_resolution]) == n_of_time_groups

            # for each time group, check if number of channels == -4 dimension of volume_arr
            for time in range(n_of_time_groups):
                n_of_channel_groups = volume_arr.shape[-4]
                assert (
                    len(volume_gr[volume_arr_resolution][time]) == n_of_channel_groups
                )

                # key error 0
                # for each channel, check if shape is equal to shape of volume arr with swapaxes
                # channel has a meaningful ID

                time_gr: zarr.Group = volume_gr[volume_arr_resolution][time]
                for channel_id, channel_arr in time_gr.groups():
                    # for channel in range(n_of_channel_groups):
                    assert isinstance(channel_arr, zarr.Array)
                    assert channel_arr.shape == volume_3d_arr_shape
                    # check dtype
                    assert channel_arr.dtype == volume_arr.dtype
