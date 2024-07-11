import dask.array as da
import nibabel as nib
import numpy as np
import zarr
from cellstar_preprocessor.flows.constants import VOLUME_DATA_GROUPNAME
from cellstar_preprocessor.flows.volume.helper_methods import (
    store_volume_data_in_zarr,
)
from cellstar_preprocessor.flows.zarr_methods import open_zarr
from cellstar_preprocessor.model.volume import InternalVolume


def nii_volume_preprocessing(internal_volume: InternalVolume):
    # NOTE: supports only 3D images

    zarr_structure: zarr.Group = open_zarr(internal_volume.path)

    img = nib.load(str(internal_volume.input_path.resolve()))
    data = img.get_fdata()

    print(f"Processing volume file {internal_volume.input_path}")
    dask_arr = da.from_array(data)

    # dask_arr = normalize_axis_order_mrcfile(dask_arr=dask_arr, mrc_header=header)

    # create volume data group
    volume_data_group: zarr.Group = zarr_structure.create_group(VOLUME_DATA_GROUPNAME)

    if internal_volume.quantize_dtype_str and (
        (internal_volume.volume_force_dtype in (np.uint8, np.int8))
        or (
            (internal_volume.volume_force_dtype in (np.uint16, np.int16))
            and (
                internal_volume.quantize_dtype_str.value in ["u2", "|u2", ">u2", "<u2"]
            )
        )
    ):
        print(
            f"Quantization is skipped because input volume dtype is {internal_volume.volume_force_dtype} and requested quantization dtype is {internal_volume.quantize_dtype_str.value}"
        )
        internal_volume.quantize_dtype_str = None

    store_volume_data_in_zarr(
        data=dask_arr,
        volume_data_group=volume_data_group,
        params_for_storing=internal_volume.params_for_storing,
        force_dtype=internal_volume.volume_force_dtype,
        resolution="1",
        timeframe_index="0",
        channel_id="0",
    )

    internal_volume.map_header = img.header

    print("Volume processed")
