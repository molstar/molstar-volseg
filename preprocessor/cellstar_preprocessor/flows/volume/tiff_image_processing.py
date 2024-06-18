import zarr
from cellstar_preprocessor.flows.common import (
    open_zarr_structure_from_path,
    prepare_ometiff_for_writing,
    read_ometiff_to_dask,
    set_ometiff_source_metadata,
    set_volume_custom_data,
)
from cellstar_preprocessor.flows.constants import VOLUME_DATA_GROUPNAME
from cellstar_preprocessor.flows.volume.helper_methods import (
    store_volume_data_in_zarr_stucture,
)
from cellstar_preprocessor.model.volume import InternalVolume

from cellstar_preprocessor.tools.tiff_stack_to_da_arr.tiff_stack_to_da_arr import tiff_stack_to_da_arr

def tiff_image_stack_dir_processing(internal_volume: InternalVolume):
    zarr_structure: zarr.Group = open_zarr_structure_from_path(
        internal_volume.intermediate_zarr_structure_path
    )
    set_volume_custom_data(internal_volume, zarr_structure)

    # print(f"Processing volume file {internal_volume.volume_input_path}")

    # need to specify path to folder with tiff stack
    img_array = tiff_stack_to_da_arr(internal_volume.volume_input_path)
   
    volume_data_group: zarr.Group = zarr_structure.create_group(VOLUME_DATA_GROUPNAME)

    store_volume_data_in_zarr_stucture(
        data=img_array,
        volume_data_group=volume_data_group,
        params_for_storing=internal_volume.params_for_storing,
        force_dtype=internal_volume.volume_force_dtype,
        resolution="1",
        time_frame='0',
        channel='0',
        quantize_dtype_str=internal_volume.quantize_dtype_str
    )
    print("Volume processed")
