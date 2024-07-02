
from cellstar_preprocessor.model.segmentation import InternalSegmentation

def mask_segmentation_metadata_preprocessing(
    s: InternalSegmentation,
):
    s.set_segmentation_lattices_metadata()