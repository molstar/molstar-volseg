from cellstar_preprocessor.flows.segmentation.helper_methods import (
    check_if_omezarr_has_labels,
)
from cellstar_preprocessor.flows.segmentation.geometric_segmentation_preprocessing import (
    geometric_segmentation_preprocessing,
)
from cellstar_preprocessor.flows.segmentation.mask_segmentation_preprocessing import (
    mask_segmentation_preprocessing,
)
from cellstar_preprocessor.flows.segmentation.ometiff_segmentation_processing import (
    ometiff_segmentation_processing,
)
from cellstar_preprocessor.flows.segmentation.omezarr_segmentations_preprocessing import (
    omezarr_segmentations_preprocessing,
)
from cellstar_preprocessor.flows.segmentation.segmentation_downsampling import (
    segmentation_downsampling,
)
from cellstar_preprocessor.flows.segmentation.sff_segmentation_preprocessing import (
    sff_segmentation_preprocessing,
)
from cellstar_db.models import InputKind
from cellstar_preprocessor.model.segmentation import InternalSegmentation


def process_segmentation(s: InternalSegmentation):
    kind = s.input_kind
    if kind == InputKind.sff:
        sff_segmentation_preprocessing(s)
        segmentation_downsampling(s)
    elif kind == InputKind.mask:
        mask_segmentation_preprocessing(s)
        segmentation_downsampling(s)
    elif kind == InputKind.geometric_segmentation:
        geometric_segmentation_preprocessing(s)
    elif kind == InputKind.ometiff_segmentation:
        ometiff_segmentation_processing(s)
    elif kind == InputKind.omezarr:
        if check_if_omezarr_has_labels(s):
            omezarr_segmentations_preprocessing(s)
