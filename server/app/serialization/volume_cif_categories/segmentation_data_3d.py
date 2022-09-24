from typing import Callable, Optional, Union

import numpy as np
from ciftools.binary.encoding.base.cif_encoder_base import CIFEncoderBase
from ciftools.binary.encoding.data_types import DataType, DataTypeEnum
from ciftools.binary.encoding.impl.binary_cif_encoder import BinaryCIFEncoder
from ciftools.binary.encoding.impl.encoders.byte_array import ByteArrayCIFEncoder
from ciftools.binary.encoding.impl.encoders.interval_quantization import IntervalQuantizationCIFEncoder
from ciftools.binary.encoding.impl.encoders.run_length import RunLengthCIFEncoder
from ciftools.cif_format import ValuePresenceEnum
from ciftools.writer.base import CategoryWriter, CategoryWriterProvider, FieldDesc
from ciftools.writer.fields import number_field

from app.serialization.volume_cif_categories.common import CategoryDesc, CategoryDescImpl


class CategoryWriter_SegmentationData3d(CategoryWriter):
    def __init__(self, ctx: np.ndarray, count: int, category_desc: CategoryDesc):
        self.data = ctx
        self.count = count
        self.desc = category_desc


class CategoryWriterProvider_SegmentationData3d(CategoryWriterProvider):
    def _decide_encoder(self, ctx: np.ndarray) -> tuple[BinaryCIFEncoder, np.dtype]:
        data_type = DataType.from_dtype(ctx.dtype)

        encoders: list[CIFEncoderBase] = [ByteArrayCIFEncoder()]

        if data_type == DataTypeEnum.Float32 or data_type == DataTypeEnum.Float64:
            print(
                "Encoder for SegmentationData3d was chosen as IntervalQuantizationCIFEncoder for dataType = "
                + str(data_type)
            )
            data_min: int = ctx.min(initial=ctx[0])
            data_max: int = ctx.max(initial=ctx[0])
            interval_quantization = IntervalQuantizationCIFEncoder(data_min, data_max, 255, DataTypeEnum.Uint8)
            encoders.insert(0, interval_quantization)
        else:
            print("Encoder for SegmentationData3d was chosen as RunLengthCIFEncoder for dataType = " + str(data_type))
            encoders.insert(0, RunLengthCIFEncoder())

        typed_array = DataType.to_dtype(data_type)

        return BinaryCIFEncoder(encoders), typed_array

    def category_writer(self, ctx: np.ndarray) -> CategoryWriter:
        ctx = np.ravel(ctx)
        field_desc: list[FieldDesc] = Fields_SegmentationData3d(*self._decide_encoder(ctx)).fields
        return CategoryWriter_SegmentationData3d(ctx, ctx.size, CategoryDescImpl("segmentation_data_3d", field_desc))


def number_field_segmentation3d(
    *,
    name: str,
    value: Callable[[np.ndarray, int], Optional[Union[int, float]]],
    dtype: np.dtype,
    encoder: Callable[[np.ndarray], BinaryCIFEncoder],
    presence: Optional[Callable[[np.ndarray, int], Optional[ValuePresenceEnum]]] = None,
) -> FieldDesc:
    return number_field(name=name, value=value, dtype=dtype, encoder=encoder, presence=presence)


class Fields_SegmentationData3d:
    def _value(self, volume: np.ndarray, index: int):
        return volume[index]

    def __init__(self, encoder: BinaryCIFEncoder, dtype: np.dtype):
        self.fields: list[FieldDesc] = [
            number_field_segmentation3d(name="values", value=self._value, encoder=lambda d: encoder, dtype=dtype)
        ]
