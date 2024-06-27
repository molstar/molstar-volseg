from uuid import uuid4

import numpy as np
import zarr
from cellstar_preprocessor.flows.common import open_zarr_structure_from_path
from cellstar_preprocessor.flows.constants import VOLUME_DATA_GROUPNAME
from cellstar_preprocessor.flows.volume.volume_downsampling import volume_downsampling
from cellstar_preprocessor.model.input import (
    DownsamplingParams,
    EntryData,
    QuantizationDtype,
    StoringParams,
)
from cellstar_preprocessor.model.volume import InternalVolume
from cellstar_preprocessor.tests.helper_methods import (
    initialize_intermediate_zarr_structure_for_tests,
    remove_intermediate_zarr_structure_for_tests,
)
from cellstar_preprocessor.tests.input_for_tests import TEST_MAP_PATH


def test_volume_downsampling():
    unique_folder_name = str(uuid4())
    p = initialize_intermediate_zarr_structure_for_tests(unique_folder_name)
    internal_volume = InternalVolume(
        intermediate_zarr_structure_path=p,
        input_path=TEST_MAP_PATH,
        params_for_storing=StoringParams(),
        volume_force_dtype="f2",
        downsampling_parameters=DownsamplingParams(),
        entry_data=EntryData(
            entry_id="emd-1832",
            source_db="emdb",
            source_db_id="emd-1832",
            source_db_name="emdb",
        ),
        quantize_dtype_str=QuantizationDtype.u1,
        quantize_downsampling_levels=(1,),
    )

    zarr_structure: zarr.Group = open_zarr_structure_from_path(
        internal_volume.intermediate_zarr_structure_path
    )

    # create synthetic array filled with ones
    arr = zarr_structure.create_dataset(
        f"{VOLUME_DATA_GROUPNAME}/1/0/0", shape=(64, 64, 64), fill_value=1
    )

    volume_downsampling(internal_volume=internal_volume)
    # test if there is just one downsampling and if it has shape=32,32,32 and values=1

    assert "2/0/0" in zarr_structure[VOLUME_DATA_GROUPNAME]
    assert (
        zarr_structure[f"{VOLUME_DATA_GROUPNAME}/2/0/0"][...]
        == np.ones(shape=(32, 32, 32), dtype=internal_volume.volume_force_dtype)
    ).all()

    remove_intermediate_zarr_structure_for_tests(p)
