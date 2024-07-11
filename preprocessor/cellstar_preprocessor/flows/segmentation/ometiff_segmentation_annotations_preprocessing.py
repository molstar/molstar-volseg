from uuid import uuid4

import seaborn as sns
import zarr
from cellstar_db.models import (
    AnnotationsMetadata,
    DescriptionData,
    SegmentAnnotationData,
    SegmentationKind,
    TargetId,
)
from cellstar_preprocessor.flows.constants import LATTICE_SEGMENTATION_DATA_GROUPNAME
from cellstar_preprocessor.flows.zarr_methods import open_zarr
from cellstar_preprocessor.model.segmentation import InternalSegmentation


def _get_allencell_cell_stage(root: zarr.Group):
    return root.attrs["extra_data"]["cell_stage"]


def ometiff_segmentation_annotations_preprocessing(
    internal_segmentation: InternalSegmentation,
):
    # root = open_zarr(internal_segmentation.path)
    # # this is based on Channels which is wrong in many cases

    # get_ometiff_source_metadata(internal_segmentation)
    # d: AnnotationsMetadata = root.attrs[ANNOTATIONS_DICT_NAME]

    # # PLAN: iterate over lattices
    # # single value 255 - hardcoded (it is in specification)
    # # name - lattice name
    # # that is it
    # # create palette

    # # NOTE: in general case assume that Channels are wrong
    # # create palette based on custom_data?
    # # artificial channel ids are there?
    # # now they are

    # palette = sns.color_palette(
    #     None,
    #     len(list(internal_segmentation.custom_data["segmentation_ids_mapping"].keys())),
    # )

    # # palette = sns.color_palette(None, len(ometiff_metadata['Channels'].keys()))

    # # TODO: handle cell stage based on custom data
    # # cell_stage = _get_allencell_cell_stage(root)
    # # d['name'] = f'Cell stage: {cell_stage}'

    # # each has its own color from palette
    # # does not matter which
    # count = 0

    # for label_gr_name, label_gr in root[LATTICE_SEGMENTATION_DATA_GROUPNAME].groups():
    #     # each label group is lattice id
    #     pass

    #     # NOTE: hardcoded in specs
    #     label_value = 255
    #     # TODO: no color - generate palette above the loop
    #     # ind_label_color_rgba = ind_label_meta["rgba"]
    #     # # color
    #     # ind_label_color_fractional = [i / 255 for i in ind_label_color_rgba]
    #     ind_label_color_fractional = [
    #         palette[count][0],
    #         palette[count][1],
    #         palette[count][2],
    #         1.0,
    #     ]
    #     # need to create two things: description and segment annotation
    #     # create description
    #     description_id = str(uuid4())
    #     target_id = TargetId(
    #         segment_id=label_value,
    #         segmentation_id=str(label_gr_name),
    #     )

    #     time = 0
    #     description = DescriptionData(
    #         id=description_id,
    #         target_kind="lattice",
    #         details=None,
    #         is_hidden=None,
    #         metadata=None,
    #         time=time,
    #         name=label_gr_name,
    #         external_references=[],
    #         target_id=target_id,
    #     )

    #     segment_annotation = SegmentAnnotationData(
    #         id=str(uuid4()),
    #         color=ind_label_color_fractional,
    #         segmentation_id=str(label_gr_name),
    #         segment_id=label_value,
    #         segment_kind=SegmentationKind.lattice,
    #         time=time,
    #     )
    #     d["descriptions"][description_id] = description
    #     d["segment_annotations"].append(segment_annotation)

    #     count = count + 1

    # root.attrs[ANNOTATIONS_DICT_NAME] = d
    # return d
    pass