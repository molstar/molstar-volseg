import numpy as np
from ciftools.binary.encoding.impl.binary_cif_encoder import BinaryCIFEncoder
from ciftools.binary.encoding.data_types import DataType, DataTypeEnum
from ciftools.binary.encoding.base.cif_encoder_base import CIFEncoderBase
from ciftools.binary.encoding.impl.encoders.byte_array import ByteArrayCIFEncoder
from ciftools.writer.base import CategoryWriter, CategoryWriterProvider, FieldDesc

from volume_server.src.preprocessed_volume_to_cif.implementations.ciftools_converter.Categories._writer import CategoryDesc, \
    CategoryDescImpl
from volume_server.src.preprocessed_volume_to_cif.implementations.ciftools_converter.Categories.volume_data_3d_info.Fields import \
    Fields_VolumeData3dInfo
from volume_server.src.preprocessed_volume_to_cif.implementations.ciftools_converter.Categories.volume_data_3d_info.volume_info import \
    VolumeInfo


class CategoryWriter_VolumeData3dInfo(CategoryWriter):
    def __init__(self, ctx: VolumeInfo, count: int, category_desc: CategoryDesc):
        self.data = ctx
        self.count = count
        self.desc = category_desc


class CategoryWriterProvider_VolumeData3dInfo(CategoryWriterProvider):
    def _decide_encoder(self, ctx: VolumeInfo) -> tuple[BinaryCIFEncoder, np.dtype]:
        encoders: list[CIFEncoderBase] = [ByteArrayCIFEncoder()]
        typed_array = DataType.to_dtype(DataTypeEnum.Int8)

        return BinaryCIFEncoder(encoders), typed_array

    def category_writer(self, ctx: VolumeInfo) -> CategoryWriter:
        encoder = self._decide_encoder(ctx)
        field_desc: list[FieldDesc] = Fields_VolumeData3dInfo(ctx).fields
        return CategoryWriter_VolumeData3dInfo(ctx, 1, CategoryDescImpl("volume_data_3d_info", field_desc))
