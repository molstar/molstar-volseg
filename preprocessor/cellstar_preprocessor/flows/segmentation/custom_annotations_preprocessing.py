import json
from pathlib import Path

from cellstar_db.models import AnnotationsMetadata
from cellstar_preprocessor.flows.common import (
    update_dict,
)
from cellstar_preprocessor.flows.zarr_methods import open_zarr


def custom_annotations_preprocessing(
    input_path: Path, intermediate_zarr_structure_path: Path
):
    root = open_zarr(intermediate_zarr_structure_path)
    with open(str(input_path.absolute()), "r", encoding="utf-8") as f:
        d: AnnotationsMetadata = json.load(f)
        # TODO: check if conforms to datamodel
        current_d: AnnotationsMetadata = root.attrs["annotations_dict"]
        # 1. Updating segment list
        if "segmentation_lattices" in d:
            # if there are annotations already
            if current_d.segmentation_lattices:
                for lattice in current_d.segmentation_lattices:
                    old_segment_list = lattice["segment_list"]
                    to_be_added_segment_list = list(
                        filter(
                            lambda x: x["lattice_id"] == lattice["lattice_id"],
                            d.segmentation_lattices,
                        )
                    )[0]["segment_list"]

                    to_be_added_segment_ids = [
                        segment["id"] for segment in to_be_added_segment_list
                    ]
                    list_1 = [
                        segment
                        for segment in old_segment_list
                        if segment["id"] not in to_be_added_segment_ids
                    ]

                    # list_1 - old segments that should not be modified, we do not touch them
                    # but we need to compare each segment in segments to be modified
                    # with segments from to_be_added_segment_list

                    segments_to_be_modified = [
                        segment
                        for segment in old_segment_list
                        if segment["id"] in to_be_added_segment_ids
                    ]

                    for segment in segments_to_be_modified:
                        new_segment_data = list(
                            filter(
                                lambda x: x["id"] == segment["id"],
                                to_be_added_segment_list,
                            )
                        )[0]
                        update_dict(segment, new_segment_data)
                        # for k, v in new_segment_data.items():
                        #     if k == "biological_annotation":
                        #         for k1, v1 in new_segment_data[k].items():
                        #             segment[k][k1] = v1
                        #     else:
                        #         segment[k] = v

                    updated_segment_list = list_1 + segments_to_be_modified
                    lattice["segment_list"] = updated_segment_list
            else:
                current_d.segmentation_lattices = d.segmentation_lattices

        # 2. Updating other information
        if "details" in d:
            current_d["details"] = d["details"]
        if "name" in d:
            current_d["name"] = d["name"]
        if "entry_id" in d:
            current_d.entry_id = d.entry_id
        if d.volume_channels_annotations is not None:
        # if "volume_channels_annotations" in d:
            old_volume_channels_annotations_list = current_d.volume_channels_annotations
            to_be_added_volume_channels_annotations_list = d.volume_channels_annotations

            to_be_added_channel_ids = [
                channel.channel_id
                for channel in to_be_added_volume_channels_annotations_list
            ]
            new_list = [
                channel
                for channel in old_volume_channels_annotations_list
                if channel.channel_id not in to_be_added_channel_ids
            ]
            updated_vol_ch_ann_list = (
                new_list + to_be_added_volume_channels_annotations_list
            )

            current_d.volume_channels_annotations = updated_vol_ch_ann_list

        root.attrs["annotations_dict"] = current_d

    print("Annotations updated")
