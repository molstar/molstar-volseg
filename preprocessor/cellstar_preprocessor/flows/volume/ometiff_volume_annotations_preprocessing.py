import seaborn as sns
from cellstar_db.models import Annotations, EntryId, VolumeChannelAnnotation
from cellstar_preprocessor.flows.zarr_methods import open_zarr
from cellstar_preprocessor.model.volume import InternalVolume


def _get_ome_tiff_channel_annotations(
    volume_channels_annotations: list[VolumeChannelAnnotation],
    channel_ids_dict: dict[str, str],
):
    palette = sns.color_palette(None, len(list(channel_ids_dict.keys())))

    for i, channel_id in channel_ids_dict.items():
        idx = int(i)
        color = [palette[idx][0], palette[idx][1], palette[idx][2], 1.0]
        print(f"Color: {color} for channel {channel_id}")
        volume_channels_annotations.append(
            VolumeChannelAnnotation(
                channel_id=channel_id, color=color, label=channel_id
            )
        )


def ometiff_volume_annotations_preprocessing(v: InternalVolume):
    root = open_zarr(v.path)

    v.custom_data["dataset_specific_data"]["ometiff"][
        "ometiff_source_metadata"
    ]

    # channel_ids_dict = _get_ome_tiff_channel_ids_dict(root, v)

    d: Annotations = root.attrs[ANNOTATIONS_DICT_NAME]
    # _get_ome_tiff_channel_annotations(
    #     volume_channels_annotations=d.volume_channels_annotations,
    #     channel_ids_dict=channel_ids_dict,
    # )

    v.set_entry_id_in_annotations()

    root.attrs[ANNOTATIONS_DICT_NAME] = d
    return d
