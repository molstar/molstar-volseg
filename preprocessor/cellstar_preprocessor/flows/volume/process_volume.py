from cellstar_preprocessor.model.volume import InternalVolume


def process_volume(v: InternalVolume):
    v.set_custom_data()
    v.prepare()
    # no channel ids
    v.set_channels_ids_mapping()
    v.postprepare()
    v.store()
    v.downsample()
    v.remove_original_resolution()
    v.remove_downsamplings()