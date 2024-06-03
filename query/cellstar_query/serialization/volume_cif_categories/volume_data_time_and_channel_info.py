from cellstar_query.serialization.data.volume_info import VolumeInfo
from cellstar_query.serialization.volume_cif_categories import encoders
from ciftools.models.writer import CIFCategoryDesc
from ciftools.models.writer import CIFFieldDesc as Field


class VolumeDataTimeAndChannelInfo(CIFCategoryDesc):
    name = "volume_data_time_and_channel_info"

    @staticmethod
    def get_row_count(_) -> int:
        return 1

    @staticmethod
    def get_field_descriptors(ctx: VolumeInfo):
        byte_array = encoders.bytearray_encoder
        return [
            # do we need time_id or actual time (with ms) here?
            Field.numbers(
                name="time_id",
                value=lambda d, i: ctx.time,
                encoder=byte_array,
                dtype="i4",
            ),
            Field.numbers(
                name="channel_id",
                value=lambda d, i: ctx.time,
                encoder=byte_array,
                dtype="i4",
            ),
        ]
