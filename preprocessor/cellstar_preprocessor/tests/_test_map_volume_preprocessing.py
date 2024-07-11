from typing import Literal
from uuid import uuid4

import pytest
import zarr
from cellstar_preprocessor.flows.constants import VOLUME_DATA_GROUPNAME
from cellstar_preprocessor.flows.volume.map_volume_preprocessing import (
    map_volume_preprocessing,
)
from cellstar_preprocessor.flows.zarr_methods import open_zarr
from cellstar_preprocessor.tests.helper_methods import (
    get_internal_XYZ_volume,
    get_internal_ZYX_volume,
    initialize_intermediate_zarr_structure_for_tests,
    remove_intermediate_zarr_structure_for_tests,
)

# artificial maps do not need


ORDERS = ["XYZ", "ZYX"]


# two maps
@pytest.mark.parametrize("order", ORDERS)
def test_map_volume_preprocessing(order: Literal["XYZ", "ZYX"]):
    # TODO: create sample internal volume with all params
    # TODO: test different functions (map preprocessing, quantization, downsampling)
    # using  the same internal volume
    unique_folder_name = str(uuid4())
    p = initialize_intermediate_zarr_structure_for_tests(unique_folder_name)
    if order == "XYZ":
        internal_volume = get_internal_XYZ_volume(p)
    elif order == "ZYX":
        internal_volume = get_internal_ZYX_volume(p)

    # internal_volume = INTERNAL_VOLUME_FOR_TESTING
    map_volume_preprocessing(v=internal_volume)

    # check if zarr structure has right format
    # 1. open zarr structure
    # 2. check if 1st level zarr group (resolution) is group and if there is just one group (1)
    # 3. check if 2nd level zarr group (time) is group and if there is just one group (0)
    # 4. check if 3rd level in zarr (channel) is array and if there is just one array (0)
    zarr_structure = open_zarr(internal_volume.path)

    assert VOLUME_DATA_GROUPNAME in zarr_structure
    volume_gr = zarr_structure[VOLUME_DATA_GROUPNAME]
    assert isinstance(volume_gr, zarr.Group)
    assert len(volume_gr) == 1

    assert "1" in volume_gr
    assert isinstance(volume_gr["1"], zarr.Group)
    assert len(volume_gr["1"]) == 1

    assert "0" in volume_gr["1"]
    assert isinstance(volume_gr["1"]["0"], zarr.Group)
    assert len(volume_gr["1"]["0"]) == 1

    assert "0" in volume_gr["1"]["0"]
    assert isinstance(volume_gr["1"]["0"]["0"], zarr.Array)

    # check dtype
    assert volume_gr["1"]["0"]["0"].dtype == internal_volume.volume_force_dtype

    # check if map header exist
    assert internal_volume.map_header is not None

    # check the data shape
    # checks also axis order since ZYX map has shape 4, 3, 2 and XYZ map has shape 2, 3, 4
    # so normalizing ZYX map will give shape 2, 3, 4
    assert volume_gr["1"]["0"]["0"].shape == (2, 3, 4)

    remove_intermediate_zarr_structure_for_tests(p)
