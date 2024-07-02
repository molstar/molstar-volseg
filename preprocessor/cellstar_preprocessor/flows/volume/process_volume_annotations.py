from cellstar_db.models import InputKind
from cellstar_preprocessor.flows.volume.ometiff_volume_annotations_preprocessing import (
    ometiff_volume_annotations_preprocessing,
)
from cellstar_preprocessor.flows.volume.omezarr_volume_annotations_preprocessing import (
    omezarr_volume_annotations_preprocessing,
)
from cellstar_preprocessor.model.volume import InternalVolume


def process_volume_annotations(v: InternalVolume):
    kind = v.input_kind
    # TODO: volume map annotations?
    if kind == InputKind.ometiff_image:
        ometiff_volume_annotations_preprocessing(v)
    elif kind == InputKind.omezarr:
        omezarr_volume_annotations_preprocessing(v)
