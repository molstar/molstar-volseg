import zarr
from cellstar_preprocessor.flows.common import (
    open_zarr_structure_from_path,
    prepare_ometiff_for_writing,
    read_ometiff_to_dask,
    set_ometiff_source_metadata,
    set_volume_custom_data,
)
from cellstar_preprocessor.flows.constants import VOLUME_DATA_GROUPNAME
from cellstar_preprocessor.flows.volume._helper_methods import (
    store_volume_data_in_zarr_stucture,
)
from cellstar_preprocessor.model.volume import InternalVolume


def ometiff_volume_preprocessing(internal_volume: InternalVolume):
    # NOTE: supports only 3D images

    zarr_structure: zarr.Group = open_zarr_structure_from_path(
        internal_volume.intermediate_zarr_structure_path
    )
    set_volume_custom_data(internal_volume, zarr_structure)

    # print(f"Processing volume file {internal_volume.volume_input_path}")

    img_array, metadata, xml_metadata = read_ometiff_to_dask(internal_volume)

    prepared_data, artificial_channel_ids = prepare_ometiff_for_writing(
        img_array, metadata, internal_volume
    )

    volume_data_group: zarr.Group = zarr_structure.create_group(VOLUME_DATA_GROUPNAME)

    set_ometiff_source_metadata(internal_volume, metadata)

    # NOTE: at that point internal_volume.custom_data should exist
    # as it is filled by one of three ways

    # TODO: set internal_volume.custom_data['channel_ids_mapping'] to artificial
    # if it does not exist
    if "channel_ids_mapping" not in internal_volume.custom_data:
        internal_volume.custom_data["channel_ids_mapping"] = artificial_channel_ids

    channel_ids_mapping: dict[str, str] = internal_volume.custom_data[
        "channel_ids_mapping"
    ]
    for data_item in prepared_data:
        dask_arr = data_item["data"]
        channel_number = data_item["channel_number"]
        channel_id = channel_ids_mapping[str(channel_number)]
        store_volume_data_in_zarr_stucture(
            data=dask_arr,
            volume_data_group=volume_data_group,
            params_for_storing=internal_volume.params_for_storing,
            force_dtype=internal_volume.volume_force_dtype,
            resolution="1",
            time_frame=str(data_item["time"]),
            channel=channel_id,
        )
    print("Volume processed")
