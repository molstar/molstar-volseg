from cellstar_db.models import AssetKind
from cellstar_preprocessor.flows.volume.ometiff_volume_annotations_preprocessing import (
    ometiff_volume_annotations_preprocessing,
)
from cellstar_preprocessor.flows.volume.omezarr_volume_annotations_preprocessing import (
    omezarr_volume_annotations_preprocessing,
)
from cellstar_preprocessor.model.volume import InternalVolume


def process_volume_annotations(v: InternalVolume):
    # v.set_entry_id_in_metadata()
    # v.set_volumes_metadata()
    # v.remove_original_resolution()
    # v.remove_downsamplings()
    v.set_entry_id_in_annotations()
    a = v.get_annotations()
    v.set_volume_channel_annotations()
    # set
    # channel_ids_dict = _get_ome_tiff_channel_ids_dict(root, v)

    # d: Annotations = root.attrs[ANNOTATIONS_DICT_NAME]
    # _get_ome_tiff_channel_annotations(
    #     volume_channels_annotations=d.volume_channels_annotations,
    #     channel_ids_dict=channel_ids_dict,
    # )

    # v.set_entry_id_in_annotations()

    # root.attrs[ANNOTATIONS_DICT_NAME] = d
    # return d
    
    # kind = v.input_kind
    # # TODO: volume map annotations?
    # if kind == AssetKind.ometiff_image:
    #     ometiff_volume_annotations_preprocessing(v)
    # elif kind == AssetKind.omezarr:
    #     omezarr_volume_annotations_preprocessing(v)
    # # elif kind == InputKind.tiff_image_stack_dir:
    # #     raise NotImplementedError()
