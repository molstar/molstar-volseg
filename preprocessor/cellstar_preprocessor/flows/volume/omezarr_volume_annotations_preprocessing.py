from cellstar_db.models import AnnotationsMetadata, EntryId
from cellstar_preprocessor.flows.common import (
    get_channel_annotations,
)
from cellstar_preprocessor.flows.zarr_methods import open_zarr
from cellstar_preprocessor.model.volume import InternalVolume


def omezarr_volume_annotations_preprocessing(v: InternalVolume):
    a = v.get_annotations()
    a.entry_id = EntryId(
        source_db_id=v.entry_data.source_db_id,
        source_db_name=v.entry_data.source_db_name,
    )
    ome_zarr_root = open_zarr(v.input_path)
    a.volume_channels_annotations = get_channel_annotations(ome_zarr_root.attrs)
    v.set_annotations(a)
    return a
