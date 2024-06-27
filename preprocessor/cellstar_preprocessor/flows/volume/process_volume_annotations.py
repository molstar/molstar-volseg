
from cellstar_preprocessor.flows.volume.ometiff_volume_annotations_preprocessing import extract_ome_tiff_image_annotations
from cellstar_preprocessor.flows.volume.extract_omezarr_volume_annotations import extract_omezarr_volume_annotations
from cellstar_preprocessor.model.input import InputKind
from cellstar_preprocessor.model.volume import InternalVolume


def process_volume_annotations(v: InternalVolume):
    kind = v.input_kind
    # TODO: volume map annotations?
    if kind == InputKind.ometiff_image:
        extract_ome_tiff_image_annotations(v)
    elif kind == InputKind.omezarr:
        extract_omezarr_volume_annotations(v)
