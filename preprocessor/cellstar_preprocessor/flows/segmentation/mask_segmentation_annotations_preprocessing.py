from uuid import uuid4

import seaborn as sns
from cellstar_db.models import (
    AnnotationsMetadata,
    DescriptionData,
    EntryId,
    SegmentAnnotationData,
    TargetId,
)
from cellstar_preprocessor.flows.zarr_methods import open_zarr
from cellstar_preprocessor.flows.constants import LATTICE_SEGMENTATION_DATA_GROUPNAME
from cellstar_preprocessor.model.segmentation import InternalSegmentation


def _get_segment_name_from_mapping(
    mapping: dict[str, dict[str, str]], lattice_id: str, segment_id: str
):
    # default segment name if no segmentation or no segment in mapping
    if lattice_id in mapping:
        if segment_id in mapping[lattice_id]:
            return mapping[lattice_id][segment_id]
        else:
            return f"Segment {segment_id}"
    else:
        return f"Segment {segment_id}"


def mask_segmentation_annotations_preprocessing(
    internal_segmentation: InternalSegmentation,
):
    # segm_arr = root[SEGMENTATION_DATA_GROUPNAME][0][0][0][0]

    root = open_zarr(
        internal_segmentation.path
    )
    d: AnnotationsMetadata = root.attrs["annotations_dict"]

    d["entry_id"] = EntryId(
        source_db_id=internal_segmentation.entry_data.source_db_id,
        source_db_name=internal_segmentation.entry_data.source_db_name,
    )

    d["details"] = (
        f"Segmentation of {internal_segmentation.entry_data.source_db_id} based on EMDB mask(s)"
    )
    d["name"] = (
        f"Segmentation of {internal_segmentation.entry_data.source_db_id} based on EMDB mask(s)"
    )

    # create palette of length = lattices x segments
    # have count variable = 0
    # each time you take color palette you take 'count' and then increment count
    # by 1
    palette_length = 0
    for lattice_id in internal_segmentation.value_to_segment_id_dict:
        value_to_segment_id_dict_for_lat: dict = (
            internal_segmentation.value_to_segment_id_dict[lattice_id]
        )
        palette_length = palette_length + len(
            list(value_to_segment_id_dict_for_lat.keys())
        )

    print(f"Palette length is {palette_length}")

    palette = sns.color_palette(None, palette_length)

    # should create this mapping for all lattices not mentioned in
    if "custom_segment_ids_mapping" not in internal_segmentation.custom_data:
        # list_of_sesgmentation_pathes: list[Path] = internal_segmentation.segmentation_input_path
        # internal_segmentation.custom_data['segmentation_ids_mapping'] = {s.stem : s.stem for s in list_of_sesgmentation_pathes}
        # TODO: create from internal_segmentation.value_to_segment_id_dict[lattice_id]
        internal_segmentation.custom_data["custom_segment_ids_mapping"] = {}
        for lattice_id in internal_segmentation.value_to_segment_id_dict:
            # str to int?
            # e.g. "1": 1
            # need to make "1": "Segment 1"
            # {k: '_'+ v for k,v in signames.items()}
            value_to_segment_id_dict: dict[int, int] = (
                internal_segmentation.value_to_segment_id_dict[lattice_id]
            )
            mapping_for_lattice: dict[str, str] = {
                str(k): "Segment " + str(v) for k, v in value_to_segment_id_dict.items()
            }

            internal_segmentation.custom_data["custom_segment_ids_mapping"][
                str(lattice_id)
            ] = mapping_for_lattice

    custom_segment_ids_mapping: dict[str, dict[str, str]] = (
        internal_segmentation.custom_data["custom_segment_ids_mapping"]
    )
    # segmentation_ids_mapping: dict[str, str] = internal_segmentation.custom_data['segmentation_ids_mapping']

    count = 0
    for lattice_id, lattice_gr in root[LATTICE_SEGMENTATION_DATA_GROUPNAME].groups():
        # int to int dict
        value_to_segment_id_dict = internal_segmentation.value_to_segment_id_dict[
            lattice_id
        ]
        # TODO: check if 0
        # number_of_keys = len(value_to_segment_id_dict.keys())

        for index, value in enumerate(value_to_segment_id_dict.keys()):
            segment_id = value_to_segment_id_dict[value]
            if segment_id > 0:
                # create description
                description_id = str(uuid4())
                target_id: TargetId = {
                    "segment_id": segment_id,
                    "segmentation_id": str(lattice_id),
                }
                # if segment is not in the mapping
                # or if segmentation not in the mapping
                # get default segment name
                segment_name = _get_segment_name_from_mapping(
                    internal_segmentation.custom_data["custom_segment_ids_mapping"],
                    str(lattice_id),
                    str(segment_id),
                )
                description: DescriptionData = {
                    "id": description_id,
                    "target_kind": "lattice",
                    "details": None,
                    "is_hidden": None,
                    "metadata": None,
                    "time": 0,
                    # here segment name from extra data if available
                    # 'name': f"Segment {segment_id}",
                    "name": segment_name,
                    "external_references": [],
                    "target_id": target_id,
                }
                # create segment annotation
                color: list = [
                    palette[count][0],
                    palette[count][1],
                    palette[count][2],
                    1.0,
                ]
                count = count + 1
                segment_annotation: SegmentAnnotationData = {
                    "id": str(uuid4()),
                    "color": color,
                    "segmentation_id": str(lattice_id),
                    "segment_id": segment_id,
                    "segment_kind": "lattice",
                    "time": 0,
                }
                d["descriptions"][description_id] = description
                d["segment_annotations"].append(segment_annotation)

    root.attrs["annotations_dict"] = d
    print("Annotations extracted")
    return d
