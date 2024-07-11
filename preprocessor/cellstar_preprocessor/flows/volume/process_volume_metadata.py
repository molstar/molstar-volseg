from cellstar_db.models import AssetKind
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


def process_volume_metadata(v: InternalVolume):
    v.set_entry_id_in_metadata()
    v.set_volumes_metadata()
    v.remove_original_resolution()
    v.remove_downsamplings()
    # kind = internal_volume.input_kind
    # if kind == AssetKind.map:
    #     map_volume_metadata_preprocessing(internal_volume)
    # elif kind == AssetKind.ometiff_image:
    #     ometiff_volume_metadata_preprocessing(internal_volume)
    # elif kind == AssetKind.omezarr:
    #     omezarr_volume_metadata_preprocessing(internal_volume)
    # elif kind == AssetKind.tiff_image_stack_dir:
    #     tiff_image_stack_dir_metadata_preprocessing(internal_volume)
