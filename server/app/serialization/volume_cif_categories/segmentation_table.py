import numpy as np

from ciftools.binary.encoding.base.cif_encoder_base import CIFEncoderBase
from ciftools.binary.encoding.data_types import DataType, DataTypeEnum
from ciftools.binary.encoding.impl.binary_cif_encoder import BinaryCIFEncoder
from ciftools.binary.encoding.impl.encoders.byte_array import ByteArrayCIFEncoder
from ciftools.writer.base import FieldDesc
from ciftools.writer.fields import number_field, FieldArrays

from app.serialization.data.segment_set_table import SegmentSetTable
from app.serialization.volume_cif_categories.common import CategoryWriterProviderBase
from app.serialization.volume_cif_categories import encoders


class CategoryWriterProvider_SegmentationDataTable(CategoryWriterProviderBase[SegmentSetTable]):
    category_name = 'segmentation_data_table'

    def get_row_count(self, ctx: SegmentSetTable) -> int:
        return ctx.size

    def get_field_descriptors(self, ctx: SegmentSetTable) -> list[FieldDesc]:
        # TODO: determine proper encoding (and dtype?)
        dtype = DataType.to_dtype(DataTypeEnum.Int32)
        return [
            number_field(name="set_id", arrays=lambda d: FieldArrays(np.array(d.set_id)), dtype=dtype, encoder=encoders.delta_rl_encoder),
            number_field(name="segment_id", arrays=lambda d: FieldArrays(np.array(d.segment_id)), dtype=dtype, encoder=encoders.bytearray_encoder),
        ]
