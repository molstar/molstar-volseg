from cellstar_db.models import AssetKind
from cellstar_preprocessor.flows.segmentation.tiff_segmentation_stack_dir_metadata_preprocessing import (
    tiff_segmentation_stack_dir_metadata_preprocessing,
)
from cellstar_preprocessor.flows.segmentation.geometric_segmentation_annotations_preprocessing import (
    geometric_segmentation_annotations_preprocessing,
)
from cellstar_preprocessor.flows.segmentation.mask_segmentation_metadata_preprocessing import (
    mask_segmentation_metadata_preprocessing,
)
from cellstar_preprocessor.flows.segmentation.omezarr_segmentation_metadata_preprocessing import (
    omezarr_segmentation_metadata_preprocessing,
)
from cellstar_preprocessor.flows.segmentation.sff_segmentation_metadata_preprocessing import (
    sff_segmentation_metadata_preprocessing,
)
from cellstar_preprocessor.flows.volume.ometiff_volume_metadata_preprocessing import (
    ometiff_volume_metadata_preprocessing,
)
from cellstar_preprocessor.model.segmentation import InternalSegmentation


def process_segmentation_metadata(s: InternalSegmentation):
    kind = s.input_kind
    if kind == AssetKind.sff:
        sff_segmentation_metadata_preprocessing(s)
    elif kind == AssetKind.mask:
        mask_segmentation_metadata_preprocessing(s)
    elif kind == AssetKind.geometric_segmentation:

        geometric_segmentation_annotations_preprocessing(s)
    elif kind == AssetKind.ometiff_segmentation:
        ometiff_volume_metadata_preprocessing(s)
    elif kind == AssetKind.omezarr:
        omezarr_segmentation_metadata_preprocessing(s)
    elif kind == AssetKind.tiff_segmentation_stack_dir:
        # tiff_s
        tiff_segmentation_stack_dir_metadata_preprocessing(s)
