import numpy as np
from ciftools.binary.encoding.impl.binary_cif_encoder import BinaryCIFEncoder
from ciftools.binary.encoding.data_types import DataType, DataTypeEnum
from ciftools.binary.encoding.base.cif_encoder_base import CIFEncoderBase
from ciftools.binary.encoding.impl.encoders.byte_array import ByteArrayCIFEncoder
from ciftools.writer.base import CategoryWriter, CategoryWriterProvider, FieldDesc

from volume_server.src.preprocessed_volume_to_cif.implementations.ciftools_converter.Categories._writer import CategoryDesc, \
    CategoryDescImpl
from volume_server.src.preprocessed_volume_to_cif.implementations.ciftools_converter.Categories.segmentation_table.Fields import \
    Fields_SegmentationDataTable


class CategoryWriter_SegmentationDataTable(CategoryWriter):
    def __init__(self, ctx: np.ndarray, count: int, category_desc: CategoryDesc):
        self.data = ctx
        self.count = count
        self.desc = category_desc


class CategoryWriterProvider_SegmentationDataTable(CategoryWriterProvider):
    def _decide_encoder(self, ctx: np.ndarray) -> tuple[BinaryCIFEncoder, np.dtype]:
        data_type = DataType.from_dtype(ctx.dtype)

        encoders: list[CIFEncoderBase] = [ByteArrayCIFEncoder()]

        #if data_type == DataTypeEnum.Float32 or data_type == DataTypeEnum.Float64:
        #    error = "Invalid data type for segmentation table: Expected not float and received " + data_type.name
        #    print(error)
        #    raise AttributeError(error)

        return BinaryCIFEncoder(encoders), DataType.to_dtype(DataTypeEnum.Int32)

    def category_writer(self, ctx: np.ndarray) -> CategoryWriter:
        field_desc: list[FieldDesc] = Fields_SegmentationDataTable(*self._decide_encoder(ctx)).fields
        return CategoryWriter_SegmentationDataTable(ctx, ctx.size, CategoryDescImpl("segmentation_data_table", field_desc))
