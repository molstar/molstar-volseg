from cellstar_preprocessor.flows.zarr_methods import open_zarr
import dask.array as da
import mrcfile
import numpy as np
import zarr
from cellstar_preprocessor.model.volume import (
    set_volume_extra_data,
)
from cellstar_preprocessor.flows.constants import VOLUME_DATA_GROUPNAME
from cellstar_preprocessor.flows.volume.helper_methods import (
    normalize_axis_order_mrcfile,
    store_volume_data_in_zarr_stucture,
)
from cellstar_preprocessor.model.volume import InternalVolume


def map_volume_preprocessing(v: InternalVolume):
    """1. normalize axis order
    2. add volume data to intermediate zarr structure
    """
    root: zarr.Group = v.get_zarr_root()

    with mrcfile.mmap(str(v.input_path.resolve()), "r+") as mrc_original:
        data: np.memmap = mrc_original.data
        if v.volume_force_dtype is not None:
            data = data.astype(v.volume_force_dtype)
        else:
            v.volume_force_dtype = data.dtype

        v.set_volume_custom_data()

        # temp hack to process rec files with cella 0 0 0
        # if mrc_original.header.cella.x == 0 and mrc_original.header.cella.y == 0 and mrc_original.header.cella.z == 0:
        if "voxel_size" in v.custom_data:
            # TODO: this is probably wrong
            mrc_original.voxel_size = 1 * v.custom_data.voxel_size

        header = mrc_original.header

    print(f"Processing volume file {v.input_path}")
    dask_arr = da.from_array(data)
    dask_arr = normalize_axis_order_mrcfile(dask_arr=dask_arr, mrc_header=header)

    # create volume data group
    volume_data_group: zarr.Group = root.create_group(VOLUME_DATA_GROUPNAME)

    if v.quantize_dtype_str and (
        (v.volume_force_dtype in (np.uint8, np.int8))
        or (
            (v.volume_force_dtype in (np.uint16, np.int16))
            and (
                v.quantize_dtype_str.value in ["u2", "|u2", ">u2", "<u2"]
            )
        )
    ):
        print(
            f"Quantization is skipped because input volume dtype is {v.volume_force_dtype} and requested quantization dtype is {v.quantize_dtype_str.value}"
        )
        v.quantize_dtype_str = None

    store_volume_data_in_zarr_stucture(
        data=dask_arr,
        volume_data_group=volume_data_group,
        params_for_storing=v.params_for_storing,
        force_dtype=v.volume_force_dtype,
        resolution="1",
        time_frame="0",
        channel="0",
    )

    v.map_header = header

    print("Volume processed")
