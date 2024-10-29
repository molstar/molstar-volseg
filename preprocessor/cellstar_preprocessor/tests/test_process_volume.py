from cellstar_db.models import AxisName, AssetKind
from cellstar_preprocessor.flows.volume.process_volume import process_volume
from cellstar_preprocessor.tests.test_context import TestContext, context_for_tests
import pytest
import zarr
from cellstar_preprocessor.flows.constants import VOLUME_DATA_GROUPNAME
from cellstar_preprocessor.flows.zarr_methods import open_zarr
from cellstar_preprocessor.tests.helper_methods import (
    get_internal_volume_from_input,
)
from cellstar_preprocessor.tests.input_for_tests import (
    MAP_TEST_INPUTS,
    OMETIFF_IMAGE_TEST_INPUTS,
    OMEZARR_TEST_INPUTS,
    TIFF_IMAGE_STACK_DIR_TEST_INPUTS,
    WORKING_FOLDER_FOR_TESTS,
    TestInput,
)

VOLUME_TEST_INPUTS = OMEZARR_TEST_INPUTS + MAP_TEST_INPUTS + OMETIFF_IMAGE_TEST_INPUTS + TIFF_IMAGE_STACK_DIR_TEST_INPUTS

@pytest.mark.parametrize("volume_test_input", VOLUME_TEST_INPUTS)
def test_process_volume(volume_test_input: TestInput):
    with context_for_tests(volume_test_input, WORKING_FOLDER_FOR_TESTS) as ctx:
        ctx: TestContext
        v = get_internal_volume_from_input(
            # exists
                volume_test_input, ctx.test_input_asset_path, ctx.working_folder
            )
        process_volume(v)
        
        # unify test part
        zarr_structure = open_zarr(v.path)

        assert VOLUME_DATA_GROUPNAME in zarr_structure
        volume_gr = v.get_volume_data_group()
        assert isinstance(volume_gr, zarr.Group)
        
        # TODO:
        # globally
        # set number of channels base on asset kind
        # for ometiff image use wrapper
        # for tiffstack - 1
        
        number_of_channels = 1
        data_shape = (2, 3, 4)
        if v.input_kind == AssetKind.ometiff_image:
            w = v.get_ometiff_wrapper()
            number_of_channels = len(v.channels)
            data_shape = w.data.shape
        match v.input_kind:
            case AssetKind.map | AssetKind.ometiff_image | AssetKind.tiff_image_stack_dir:
                r = v.get_first_resolution_group(volume_gr).name
                t = v.get_first_time_group(volume_gr).name
                c = v.get_first_channel_array(volume_gr).name
                
                assert r in volume_gr
                assert isinstance(volume_gr[r], zarr.Group)
                assert len(volume_gr[r]) == 1

                assert r in volume_gr[r]
                assert isinstance(volume_gr[r][t], zarr.Group)
                
                assert len(volume_gr[r][t]) == number_of_channels
                assert c in volume_gr[r][t]
                assert isinstance(volume_gr[r][t][c], zarr.Array)

                # check dtype
                assert volume_gr[r][t][c].dtype == v.volume_force_dtype
                assert v.map_header is not None

                # check the data shape
                # checks also axis order since ZYX map has shape 4, 3, 2 and XYZ map has shape 2, 3, 4
                # so normalizing ZYX map will give shape 2, 3, 4
                assert volume_gr["1"]["0"]["0"].shape == data_shape
            
            
            # no ometiff and tiff stack cases
            case AssetKind.omezarr:
                w = v.get_omezarr_wrapper()
                axes = w.get_image_multiscale().axes
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


            case _:
                raise NotImplementedError('Test code for input kind ', v.input_kind, " has not been implemented yet")