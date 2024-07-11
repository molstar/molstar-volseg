from cellstar_db.models import EntryId
from cellstar_preprocessor.flows.zarr_methods import open_zarr
from cellstar_preprocessor.model.volume import InternalVolume


def omezarr_volume_annotations_preprocessing(v: InternalVolume):
    a = v.get_annotations()
    v.set_entry_id_in_annotations()
    a.volume_channels_annotations = v.set_volume_channel_annotations()
    v.set_annotations(a)
    return a
