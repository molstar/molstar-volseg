from typing import Callable, Optional

import numpy as np
from ciftools.binary.encoding import BinaryCIFEncoder
from ciftools.cif_format import ValuePresenceEnum
from ciftools.writer.base import FieldDesc
from ciftools.writer.fields import number_field

from db.interface.i_preprocessed_volume import IPreprocessedVolume

from ciftools.binary.encoding.impl.encoders.byte_array import BYTE_ARRAY_CIF_ENCODER
# from ciftools.binary.encoding.impl.encoders.integer_packing import BYTE_ARRAY_CIF_ENCODER
from ciftools.binary.encoding.impl.encoders.interval_quantization import IntervalQuantizationCIFEncoder
from ciftools.binary.encoding.data_types import DataType, DataTypeEnum


def number_field_volume3d(
    *,
    name: str,
    value: Callable[[np.ndarray, int], Optional[int | float]],
    dtype: np.dtype,
    encoder: Callable[[np.ndarray], BinaryCIFEncoder],
    presence: Optional[Callable[[np.ndarray, int], Optional[ValuePresenceEnum]]] = None,
) -> FieldDesc:
    return number_field(name=name, value=value, dtype=dtype, encoder=encoder, presence=presence)

class Fields_VolumeData3d:
    def _value(self, volume: np.ndarray, index: int):
        return volume[index]

    def __init__(self, encoder: BinaryCIFEncoder, dtype: np.dtype):
        # def create_encoder(d):
        #     vmin, vmax = np.min(d), np.max(d)
        #     # return BinaryCIFEncoder([IntervalQuantizationCIFEncoder(vmin, vmax, 255, DataTypeEnum.Uint8), BYTE_ARRAY_CIF_ENCODER])
        #     return BinaryCIFEncoder([BYTE_ARRAY_CIF_ENCODER])
        # # create_encoder = lambda d: BinaryCIFEncoder([IntervalQuantizationCIFEncoder(np.min(d), np.max(d), 255, DataTypeEnum.Uint8), BYTE_ARRAY_CIF_ENCODER])

        # self.fields: list[FieldDesc] = [
        #     number_field_volume3d(name="values", value=self._value, encoder=create_encoder, dtype='f4')
        # ]

        self.fields: list[FieldDesc] = [
            number_field_volume3d(name="values", value=self._value, encoder=lambda _: encoder, dtype=dtype)
        ]