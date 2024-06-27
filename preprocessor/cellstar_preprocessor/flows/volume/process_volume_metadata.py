from cellstar_preprocessor.flows.volume.map_metadata_processing import map_metadata_processing
from cellstar_preprocessor.flows.volume.extract_ometiff_image_metadata import extract_ometiff_image_metadata
from cellstar_preprocessor.flows.volume.extract_omezarr_metadata import extract_ome_zarr_metadata
from cellstar_preprocessor.flows.volume.map_preprocessing import map_preprocessing
from cellstar_preprocessor.flows.volume.ome_zarr_image_preprocessing import ome_zarr_image_preprocessing
from cellstar_preprocessor.flows.volume.ometiff_image_processing import ometiff_image_processing
from cellstar_preprocessor.flows.volume.volume_downsampling import volume_downsampling
from cellstar_preprocessor.model.input import InputKind
from cellstar_preprocessor.model.volume import InternalVolume

def process_volume_metadata(internal_volume: InternalVolume):
    kind = internal_volume.input_kind
    if kind == InputKind.map:
        map_metadata_processing(internal_volume)
    elif kind == InputKind.ometiff_image:
        extract_ometiff_image_metadata(internal_volume)
    elif kind == InputKind.omezarr:
        extract_ome_zarr_metadata(internal_volume)
