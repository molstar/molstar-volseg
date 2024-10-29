from cellstar_db.models import SegmentationKind, PrimaryDescriptor
from cellstar_preprocessor.flows.constants import MESH_SIMPLIFICATION_LEVELS_PER_ORDER, MESH_SIMPLIFICATION_N_LEVELS, TIME_INFO_STANDARD
from cellstar_preprocessor.flows.segmentation.helper_methods import make_simplification_curve
from cellstar_preprocessor.model.segmentation import InternalSegmentation


def sff_segmentation_metadata_preprocessing(
    s: InternalSegmentation,
):
    if s.primary_descriptor == PrimaryDescriptor.three_d_volume:
        s.set_segmentation_lattices_metadata()

    elif s.primary_descriptor == PrimaryDescriptor.mesh_list:
        # m = s.get_metadata()
        s.simplification_curve = make_simplification_curve(
            MESH_SIMPLIFICATION_N_LEVELS, MESH_SIMPLIFICATION_LEVELS_PER_ORDER
        )
        # data_gr = s.get_segmentation_data_group(SegmentationKind.mesh)
        # order: segment_ids, detail_lvls, time, channel, mesh_ids
        # TODO: move this to set meshes metadata as well
        s.set_meshes_metadata()
