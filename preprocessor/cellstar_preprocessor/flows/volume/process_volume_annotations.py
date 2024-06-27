from cellstar_preprocessor.flows.volume.extract_metadata_from_map import extract_metadata_from_map
from cellstar_preprocessor.flows.volume.extract_ome_tiff_image_annotations import extract_ome_tiff_image_annotations
from cellstar_preprocessor.flows.volume.extract_ometiff_image_metadata import extract_ometiff_image_metadata
from cellstar_preprocessor.flows.volume.extract_omezarr_annotations import extract_omezarr_annotations
from cellstar_preprocessor.flows.volume.extract_omezarr_metadata import extract_ome_zarr_metadata
from cellstar_preprocessor.flows.volume.map_preprocessing import map_preprocessing
from cellstar_preprocessor.flows.volume.ome_zarr_image_preprocessing import ome_zarr_image_preprocessing
from cellstar_preprocessor.flows.volume.ometiff_image_processing import ometiff_image_processing
from cellstar_preprocessor.flows.volume.volume_downsampling import volume_downsampling
from cellstar_preprocessor.model.input import InputKind
from cellstar_preprocessor.model.volume import InternalVolume

def process_volume_annotations(v: InternalVolume):
    kind = v.input_kind
    # TODO: volume map annotations?
    if kind == InputKind.ometiff_image:
        extract_ome_tiff_image_annotations(v)
    elif kind == InputKind.omezarr:
        extract_omezarr_annotations(v)
