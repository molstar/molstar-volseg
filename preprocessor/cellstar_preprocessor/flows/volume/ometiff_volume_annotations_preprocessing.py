from cellstar_preprocessor.flows.zarr_methods import open_zarr
import seaborn as sns
from cellstar_db.models import AnnotationsMetadata, EntryId, VolumeChannelAnnotation
from cellstar_preprocessor.flows.common import (
    _get_ome_tiff_channel_ids_dict,
)
from cellstar_preprocessor.model.volume import InternalVolume


def _get_ome_tiff_channel_annotations(
    volume_channels_annotations: list[VolumeChannelAnnotation], channel_ids_dict: dict[str, str]
):
    palette = sns.color_palette(None, len(list(channel_ids_dict.keys())))

    for i, channel_id in channel_ids_dict.items():
        idx = int(i)
        color = [palette[idx][0], palette[idx][1], palette[idx][2], 1.0]
        print(f"Color: {color} for channel {channel_id}")
        volume_channels_annotations.append(
            VolumeChannelAnnotation(
                channel_id=channel_id,
                color=color,
                label=channel_id
            )
        )


def ometiff_volume_annotations_preprocessing(internal_volume: InternalVolume):
    root = open_zarr(
        internal_volume.path
    )

    internal_volume.custom_data["dataset_specific_data"]["ometiff"][
        "ometiff_source_metadata"
    ]

    channel_ids_dict = _get_ome_tiff_channel_ids_dict(root, internal_volume)

    d: AnnotationsMetadata = root.attrs["annotations_dict"]
    _get_ome_tiff_channel_annotations(
        volume_channels_annotations=d.volume_channels_annotations,
        channel_ids_dict=channel_ids_dict,
    )

    d.entry_id = EntryId(
        source_db_id=internal_volume.entry_data.source_db_id,
        source_db_name=internal_volume.entry_data.source_db_name,
    )

    root.attrs["annotations_dict"] = d
    return d
