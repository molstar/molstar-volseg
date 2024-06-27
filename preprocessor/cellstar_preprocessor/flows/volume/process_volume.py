from cellstar_preprocessor.flows.volume.map_preprocessing import map_preprocessing
from cellstar_preprocessor.flows.volume.ome_zarr_image_preprocessing import ome_zarr_image_preprocessing
from cellstar_preprocessor.flows.volume.ometiff_image_processing import ometiff_image_processing
from cellstar_preprocessor.flows.volume.volume_downsampling import volume_downsampling
from cellstar_preprocessor.model.input import InputKind
from cellstar_preprocessor.model.volume import InternalVolume

def process_volume(internal_volume: InternalVolume):
    kind = internal_volume.input_kind
    if kind == InputKind.map:
        map_preprocessing(internal_volume)
        # in processing part do
        volume_downsampling(internal_volume)
    elif kind == InputKind.ometiff_image:
        ometiff_image_processing(internal_volume)
        volume_downsampling(internal_volume)
    elif kind == InputKind.omezarr:
        ome_zarr_image_preprocessing(internal_volume)
