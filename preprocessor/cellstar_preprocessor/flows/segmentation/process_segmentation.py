from cellstar_db.models import AssetKind
from cellstar_preprocessor.flows.segmentation.geometric_segmentation_preprocessing import (
    geometric_segmentation_preprocessing,
)
from cellstar_preprocessor.flows.segmentation.helper_methods import (
    check_if_omezarr_has_labels,
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
from cellstar_preprocessor.flows.segmentation.sff_segmentation_preprocessing import (
    sff_segmentation_preprocessing,
)
from cellstar_preprocessor.flows.segmentation.tiff_stack_dir_segmentation_preprocessing import (
    tiff_stack_dir_segmentation_preprocessing,
)
from cellstar_preprocessor.model.segmentation import InternalSegmentation


def process_segmentation(s: InternalSegmentation):
    s.set_custom_data()
    s.set_segmentation_ids_mapping()
    s.prepare()
    s.downsample()
    # second segmentation
    s.postprepare()
    s.remove_original_resolution()
    # TODO: uncomment
    # s.remove_downsamplings()
    s.store()
    
    
    # kind = s.input_kind
    # if kind == AssetKind.sff:
    #     sff_segmentation_preprocessing(s)
    #     segmentation_downsampling(s)
    # elif kind == AssetKind.mask:
    #     mask_segmentation_preprocessing(s)
    #     segmentation_downsampling(s)
    # elif kind == AssetKind.geometric_segmentation:
    #     geometric_segmentation_preprocessing(s)
    # elif kind == AssetKind.ometiff_segmentation:
    #     ometiff_segmentation_processing(s)
    # elif kind == AssetKind.omezarr:
    #     if check_if_omezarr_has_labels(s):
    #         omezarr_segmentations_preprocessing(s)
    # elif kind == AssetKind.tiff_segmentation_stack_dir:
    #     tiff_stack_dir_segmentation_preprocessing(s)
