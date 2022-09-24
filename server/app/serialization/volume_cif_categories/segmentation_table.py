import numpy as np
from ciftools.binary.encoding.base.cif_encoder_base import CIFEncoderBase
from ciftools.binary.encoding.data_types import DataType, DataTypeEnum
from ciftools.binary.encoding.impl.binary_cif_encoder import BinaryCIFEncoder
from ciftools.binary.encoding.impl.encoders.byte_array import ByteArrayCIFEncoder
from ciftools.writer.base import CategoryWriter, CategoryWriterProvider, FieldDesc
from ciftools.writer.fields import number_field

from app.serialization.volume_cif_categories.common import CategoryDesc, CategoryDescImpl


class CategoryWriter_SegmentationDataTable(CategoryWriter):
    def __init__(self, ctx, count: int, category_desc: CategoryDesc):
        self.data = ctx
        self.count = count
        self.desc = category_desc


class CategoryWriterProvider_SegmentationDataTable(CategoryWriterProvider):
    def _decide_encoder(self, ctx) -> tuple[BinaryCIFEncoder, np.dtype]:
        # data_type = DataType.from_dtype(ctx.dtype)

        # TODO: determine proper encoding
        encoders: list[CIFEncoderBase] = [ByteArrayCIFEncoder()]

        # if data_type == DataTypeEnum.Float32 or data_type == DataTypeEnum.Float64:
        #    error = "Invalid data type for segmentation table: Expected not float and received " + data_type.name
        #    print(error)
        #    raise AttributeError(error)

        return BinaryCIFEncoder(encoders), DataType.to_dtype(DataTypeEnum.Int32)

    def category_writer(self, ctx) -> CategoryWriter:
        field_desc: list[FieldDesc] = Fields_SegmentationDataTable(*self._decide_encoder(ctx)).fields
        return CategoryWriter_SegmentationDataTable(
            ctx, ctx["size"], CategoryDescImpl("segmentation_data_table", field_desc)
        )


class Fields_SegmentationDataTable:
    def __init__(self, encoder: BinaryCIFEncoder, dtype: np.dtype):
        self.fields: list[FieldDesc] = [
            number_field(name="set_id", value=lambda d, i: d["set_id"][i], dtype=dtype, encoder=lambda d: encoder),
            number_field(
                name="segment_id", value=lambda d, i: d["segment_id"][i], dtype=dtype, encoder=lambda d: encoder
            ),
        ]
