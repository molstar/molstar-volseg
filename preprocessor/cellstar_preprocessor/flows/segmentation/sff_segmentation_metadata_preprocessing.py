from cellstar_db.models import SegmentationKind, SegmentationPrimaryDescriptor
from cellstar_preprocessor.flows.constants import TIME_INFO_STANDARD
from cellstar_preprocessor.model.segmentation import InternalSegmentation


def sff_segmentation_metadata_preprocessing(
    s: InternalSegmentation,
):
    if s.primary_descriptor == SegmentationPrimaryDescriptor.three_d_volume:
        s.set_segmentation_lattices_metadata()

    elif s.primary_descriptor == SegmentationPrimaryDescriptor.mesh_list:
        m = s.get_metadata()
        data_gr = s.get_segmentation_data_group(SegmentationKind.mesh)
        # order: segment_ids, detail_lvls, time, channel, mesh_ids
        # TODO: move this to set meshes metadata as well
        for segmentation_id, segmentation_gr in data_gr.groups():
            m.segmentation_meshes.time_info_mapping[segmentation_id] = (
                TIME_INFO_STANDARD
            )
            m.segmentation_meshes.ids.append(segmentation_id)

        s.set_meshes_metadata()
        s.set_metadata(m)