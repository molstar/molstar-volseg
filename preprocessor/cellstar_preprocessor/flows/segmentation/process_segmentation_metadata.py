from cellstar_preprocessor.flows.segmentation.extract_annotations_from_geometric_segmentation import extract_annotations_from_geometric_segmentation
from cellstar_preprocessor.flows.segmentation.extract_metadata_from_mask import extract_metadata_from_mask
from cellstar_preprocessor.flows.segmentation.extract_metadata_from_sff_segmentation import extract_metadata_from_sff_segmentation
from cellstar_preprocessor.flows.segmentation.geometric_segmentation_preprocessing import geometric_segmentation_preprocessing
from cellstar_preprocessor.flows.segmentation.mask_segmentation_preprocessing import mask_segmentation_preprocessing
from cellstar_preprocessor.flows.segmentation.ome_zarr_labels_preprocessing import ome_zarr_labels_preprocessing
from cellstar_preprocessor.flows.segmentation.segmentation_downsampling import lattice_segmentation_downsampling
from cellstar_preprocessor.flows.segmentation.sff_preprocessing import sff_preprocessing
from cellstar_preprocessor.flows.volume.ometiff_volume_metadata_preprocessing import extract_ometiff_image_metadata
from cellstar_preprocessor.flows.volume.extract_omezarr_metadata import extract_ome_zarr_metadata
from cellstar_preprocessor.flows.volume.ometiff_segmentation_processing import ometiff_segmentation_processing
from cellstar_preprocessor.model.input import InputKind
from cellstar_preprocessor.model.segmentation import InternalSegmentation


def process_segmentation_metadata(s: InternalSegmentation):
    kind = s.input_kind
    if kind == InputKind.sff:
        extract_metadata_from_sff_segmentation(s)
    elif kind == InputKind.mask:
        extract_metadata_from_mask(s)
    elif kind == InputKind.geometric_segmentation:
        extract_annotations_from_geometric_segmentation(s)
    elif kind == InputKind.ometiff_segmentation:
        extract_ometiff_image_metadata(s)
    elif kind == InputKind.omezarr:
        extract_ome_zarr_metadata(s)