from cellstar_query.serialization.data.segment_set_table import SegmentSetTable
from cellstar_query.serialization.volume_cif_categories import encoders
from ciftools.binary.data_types import DataType, DataTypeEnum
from ciftools.models.writer import CIFCategoryDesc
from ciftools.models.writer import CIFFieldDesc as Field


class SegmentationDataTableCategory(CIFCategoryDesc):
    name = "segmentation_data_table"

    @staticmethod
    def get_row_count(ctx: SegmentSetTable) -> int:
        return ctx.size

    @staticmethod
    def get_field_descriptors(ctx: SegmentSetTable):
        # TODO: determine proper encoding (and dtype?)
        dtype = DataType.to_dtype(DataTypeEnum.Int32)
        return [
            Field[SegmentSetTable].number_array(
                name="set_id",
                array=lambda d: d.set_id,
                dtype=dtype,
                encoder=encoders.delta_rl_encoder,
            ),
            Field[SegmentSetTable].number_array(
                name="segment_id",
                array=lambda d: d.segment_id,
                dtype=dtype,
                encoder=encoders.bytearray_encoder,
            ),
        ]
