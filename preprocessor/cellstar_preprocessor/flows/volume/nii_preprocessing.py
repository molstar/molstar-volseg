import dask.array as da
import nibabel as nib
import numpy as np
import zarr
from cellstar_preprocessor.flows.common import open_zarr_structure_from_path
from cellstar_preprocessor.flows.constants import VOLUME_DATA_GROUPNAME
from cellstar_preprocessor.flows.volume.helper_methods import (
    store_volume_data_in_zarr_stucture,
)
from cellstar_preprocessor.model.volume import InternalVolume


def nii_preprocessing(internal_volume: InternalVolume):
    # NOTE: supports only 3D images

    zarr_structure: zarr.Group = open_zarr_structure_from_path(
        internal_volume.intermediate_zarr_structure_path
    )

    img = nib.load(str(internal_volume.volume_input_path.resolve()))
    data = img.get_fdata()

    print(f"Processing volume file {internal_volume.volume_input_path}")
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

    store_volume_data_in_zarr_stucture(
        data=dask_arr,
        volume_data_group=volume_data_group,
        params_for_storing=internal_volume.params_for_storing,
        force_dtype=internal_volume.volume_force_dtype,
        resolution="1",
        time_frame="0",
        channel="0",
        )

    internal_volume.map_header = img.header

    print("Volume processed")
