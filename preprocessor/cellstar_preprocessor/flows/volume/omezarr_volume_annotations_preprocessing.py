from cellstar_db.models import AnnotationsMetadata, EntryId
from cellstar_preprocessor.flows.common import (
    get_channel_annotations,
    open_zarr_structure_from_path,
)
from cellstar_preprocessor.model.volume import InternalVolume


def omezarr_volume_annotations_preprocessing(internal_volume: InternalVolume):
    ome_zarr_root = open_zarr_structure_from_path(internal_volume.input_path)
    root = open_zarr_structure_from_path(
        internal_volume.intermediate_zarr_structure_path
    )
    d: AnnotationsMetadata = root.attrs["annotations_dict"]

    d["entry_id"] = EntryId(
        source_db_id=internal_volume.entry_data.source_db_id,
        source_db_name=internal_volume.entry_data.source_db_name,
    )

    d["volume_channels_annotations"] = get_channel_annotations(ome_zarr_root.attrs)
    root.attrs["annotations_dict"] = d
    return d
