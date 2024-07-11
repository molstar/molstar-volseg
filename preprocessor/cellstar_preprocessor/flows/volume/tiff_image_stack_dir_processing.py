import zarr
from cellstar_preprocessor.flows.constants import VOLUME_DATA_GROUPNAME
from cellstar_preprocessor.flows.volume.helper_methods import (
    store_volume_data_in_zarr,
)
from cellstar_preprocessor.model.volume import InternalVolume
from cellstar_preprocessor.tools.tiff_stack_to_da_arr.tiff_stack_to_da_arr import (
    tiff_stack_to_da_arr,
)

# from cellstar_preprocessor.tools.tiff_stack_to_da_arr.tiff_stack_to_da_arr import tiff_stack_to_da_arr


def tiff_image_stack_dir_processing(i: InternalVolume):
    zarr_structure: zarr.Group = i.get_zarr_root()
    i.set_custom_data(i, zarr_structure)

    # print(f"Processing volume file {internal_volume.volume_input_path}")

    # need to specify path to folder with tiff stack
    img_array = tiff_stack_to_da_arr(i.volume_input_path)

    volume_data_group: zarr.Group = zarr_structure.create_group(VOLUME_DATA_GROUPNAME)

    store_volume_data_in_zarr(
        data=img_array,
        volume_data_group=volume_data_group,
        params_for_storing=i.params_for_storing,
        force_dtype=i.volume_force_dtype,
        resolution="1",
        timeframe_index="0",
        channel_id="0",
        # quantize_dtype_str=internal_volume.quantize_dtype_str
    )
    print("Volume processed")
