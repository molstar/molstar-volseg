from cellstar_preprocessor.model.volume import InternalVolume

def map_volume_metadata_preprocessing(v: InternalVolume):
    v.set_entry_id_in_metadata()
    v.set_volumes_metadata()
    v.remove_original_resolution()
    v.remove_downsamplings()
