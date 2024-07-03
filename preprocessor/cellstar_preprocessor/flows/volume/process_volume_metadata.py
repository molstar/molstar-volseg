from cellstar_db.models import InputKind
from cellstar_preprocessor.flows.volume.tiff_image_stack_dir_metadata_preprocessing import (
    tiff_image_stack_dir_metadata_preprocessing,
)
from cellstar_preprocessor.flows.volume.map_volume_metadata_preprocessing import (
    map_volume_metadata_preprocessing,
)
from cellstar_preprocessor.flows.volume.ometiff_volume_metadata_preprocessing import (
    ometiff_volume_metadata_preprocessing,
)
from cellstar_preprocessor.flows.volume.omezarr_volume_metadata_preprocessing import (
    omezarr_volume_metadata_preprocessing,
)
from cellstar_preprocessor.model.volume import InternalVolume


def process_volume_metadata(internal_volume: InternalVolume):
    kind = internal_volume.input_kind
    if kind == InputKind.map:
        map_volume_metadata_preprocessing(internal_volume)
    elif kind == InputKind.ometiff_image:
        ometiff_volume_metadata_preprocessing(internal_volume)
    elif kind == InputKind.omezarr:
        omezarr_volume_metadata_preprocessing(internal_volume)
    elif kind == InputKind.tiff_image_stack_dir:
        tiff_image_stack_dir_metadata_preprocessing(internal_volume)
