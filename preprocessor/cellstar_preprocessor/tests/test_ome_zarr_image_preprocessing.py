import pytest
import zarr
from cellstar_preprocessor.flows.common import open_zarr_structure_from_path
from cellstar_preprocessor.flows.constants import VOLUME_DATA_GROUPNAME
from cellstar_preprocessor.flows.volume.ome_zarr_image_preprocessing import (
    ome_zarr_image_preprocessing,
)
from cellstar_preprocessor.tests.helper_methods import get_internal_volume_from_input
from cellstar_preprocessor.tests.input_for_tests import (
    OMEZARR_TEST_INPUTS,
    WORKING_FOLDER_FOR_TESTS,
    TestInput,
)
from cellstar_preprocessor.tests.test_context import TestContext, context_for_tests


@pytest.mark.parametrize("omezar_test_input", OMEZARR_TEST_INPUTS)
def test_ome_zarr_image_preprocessing(omezar_test_input: TestInput):
    with context_for_tests(omezar_test_input, WORKING_FOLDER_FOR_TESTS) as ctx:
        ctx: TestContext
        internal_volume = get_internal_volume_from_input(
            omezar_test_input, ctx.test_file_path, ctx.intermediate_zarr_structure_path
        )

        ome_zarr_image_preprocessing(internal_volume=internal_volume)

        ome_zarr_root = zarr.open_group(internal_volume.input_path)
        root_zattrs = ome_zarr_root.attrs
        multiscales = root_zattrs["multiscales"]
        axes = multiscales[0]["axes"]

        zarr_structure = open_zarr_structure_from_path(
            internal_volume.intermediate_zarr_structure_path
        )

        assert VOLUME_DATA_GROUPNAME in zarr_structure
        volume_gr = zarr_structure[VOLUME_DATA_GROUPNAME]
        assert isinstance(volume_gr, zarr.Group)

        # check if number of resolution groups is the same as number of arrays in ome zarr
        assert len(volume_gr) == len(list(ome_zarr_root.array_keys()))

        for volume_arr_resolution, volume_arr in ome_zarr_root.arrays():
            volume_3d_arr_shape = volume_arr[...].swapaxes(-3, -1).shape[-3:]

            assert str(volume_arr_resolution) in volume_gr
            assert isinstance(volume_gr[volume_arr_resolution], zarr.Group)

            # check number of time groups
            if len(axes) == 5 and axes[0]["name"] == "t":
                n_of_time_groups = volume_arr.shape[0]
            elif len(axes) == 4 and axes[0]["name"] == "c":
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
                    assert isinstance(channel_arr, zarr.core.Array)
                    assert channel_arr.shape == volume_3d_arr_shape
                    # check dtype
                    assert channel_arr.dtype == volume_arr.dtype
