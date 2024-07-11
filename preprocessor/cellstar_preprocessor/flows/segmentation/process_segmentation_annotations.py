from cellstar_db.models import AssetKind
from cellstar_preprocessor.flows.segmentation.geometric_segmentation_annotations_preprocessing import (
    geometric_segmentation_annotations_preprocessing,
)
from cellstar_preprocessor.flows.segmentation.mask_segmentation_annotations_preprocessing import (
    mask_segmentation_annotations_preprocessing,
)
from cellstar_preprocessor.flows.segmentation.ometiff_segmentation_annotations_preprocessing import (
    ometiff_segmentation_annotations_preprocessing,
)
from cellstar_preprocessor.flows.segmentation.omezarr_segmentation_annotations_preprocessing import (
    omezarr_segmentation_annotations_preprocessing,
)
from cellstar_preprocessor.flows.segmentation.sff_segmentation_annotations_preprocessing import (
    sff_segmentation_annotations_preprocessing,
)
from cellstar_preprocessor.model.segmentation import InternalSegmentation


def process_segmentation_annotations(s: InternalSegmentation):
    kind = s.input_kind
    if kind == AssetKind.sff:
        sff_segmentation_annotations_preprocessing(s)
    elif kind == AssetKind.mask:
        mask_segmentation_annotations_preprocessing(s)
    elif kind == AssetKind.geometric_segmentation:
        geometric_segmentation_annotations_preprocessing(s)
    elif kind == AssetKind.ometiff_segmentation:
        ometiff_segmentation_annotations_preprocessing(s)
    elif kind == AssetKind.omezarr:
        omezarr_segmentation_annotations_preprocessing(s)
    elif kind == AssetKind.tiff_segmentation_stack_dir:
        mask_segmentation_annotations_preprocessing(s)
