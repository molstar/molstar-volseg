import seaborn as sns
from cellstar_db.models import AnnotationsMetadata, EntryId
from cellstar_preprocessor.flows.common import (
    _get_ome_tiff_channel_ids_dict,
    open_zarr_structure_from_path,
)
from cellstar_preprocessor.model.volume import InternalVolume


# TODO: make it work based on actual channel ids in zarr structure
# TODO: check allencel ometiff if there are valid 'channels'
def _get_ome_tiff_channel_annotations(
    volume_channel_annotations, zarr_structure, channel_ids_dict: dict[str, str]
):
    # TODO: channel ids could be list of not integers, but strings e.g.
    # palette = sns.color_palette(None, len(ome_tiff_metadata['Channels'].keys()))
    palette = sns.color_palette(None, len(list(channel_ids_dict.keys())))
    # channel_names_from_csv = []
    # if 'extra_data' in zarr_structure.attrs:
    #     channel_names_from_csv = zarr_structure.attrs['extra_data']['name_dict']['crop_raw']

    for i, channel_id in channel_ids_dict.items():
        idx = int(i)
        color = [palette[idx][0], palette[idx][1], palette[idx][2], 1.0]
        print(f"Color: {color} for channel {channel_id}")
        volume_channel_annotations.append(
            {"channel_id": channel_id, "color": color, "label": channel_id}
        )

    # for channel_id_in_ometiff_metadata, channel_key in enumerate(ome_tiff_metadata['Channels']):
    #     # TODO: channels may be absent or wrong
    #     channel = ome_tiff_metadata['Channels'][channel_key]
    #     # for now FFFFFFF
    #     # color = 'FFFFFF'
    #     color = [
    #         palette[channel_id_in_ometiff_metadata][0],
    #         palette[channel_id_in_ometiff_metadata][1],
    #         palette[channel_id_in_ometiff_metadata][2],
    #         1.0
    #     ]
    #     print(f'Color: {color} for channel {channel_key}')
    #     # TODO: check how it is encoded in some sample
    #     # if channel['Color']:
    #     #     color = _convert_hex_to_rgba_fractional(channel['Color'])
    #     label = channel['ID']
    #     if 'Name' in channel:
    #         label = channel['Name']

    #     if channel_names_from_csv:
    #         volume_channel_annotations.append(
    #             {
    #                 'channel_id': channel_names_from_csv[channel_id_in_ometiff_metadata],
    #                 'color': color,
    #                 'label': channel_names_from_csv[channel_id_in_ometiff_metadata]
    #             }
    #         )
    #     else:
    #         volume_channel_annotations.append(
    #             {
    #                 'channel_id': str(channel_id_in_ometiff_metadata),
    #                 'color': color,
    #                 'label': label
    #             }
    #         )


def extract_ome_tiff_image_annotations(internal_volume: InternalVolume):
    # d = {
    #     'entry_id': {
    #         'source_db_name': source_db_name,
    #         'source_db_id': source_db_id
    #     },
    #     # 'segment_list': [],
    #     'segmentation_lattices': [],
    #     'details': None,
    #     'volume_channels_annotations': []
    # }
    root = open_zarr_structure_from_path(
        internal_volume.intermediate_zarr_structure_path
    )

    # TODO: fix this
    # need to store ometiff source metadata somewhere
    internal_volume.custom_data["dataset_specific_data"]["ometiff"][
        "ometiff_source_metadata"
    ]

    # TODO: fix this
    # channel_ids = ometiff_custom_data['artificial_channel_ids']
    channel_ids_dict = _get_ome_tiff_channel_ids_dict(root, internal_volume)

    d: AnnotationsMetadata = root.attrs["annotations_dict"]
    _get_ome_tiff_channel_annotations(
        volume_channel_annotations=d["volume_channels_annotations"],
        zarr_structure=root,
        channel_ids_dict=channel_ids_dict,
    )

    d["entry_id"] = EntryId(
        source_db_id=internal_volume.entry_data.source_db_id,
        source_db_name=internal_volume.entry_data.source_db_name,
    )

    root.attrs["annotations_dict"] = d
    return d
