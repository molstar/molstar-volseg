from typing import Callable, Optional, Union

import numpy as np
from ciftools.src.binary.encoding.impl.binary_cif_encoder import BinaryCIFEncoder
from ciftools.src.cif_format import ValuePresenceEnum
from ciftools.src.writer.base import FieldDesc
from ciftools.src.writer.fields import number_field


def number_field_segmentation_table(
    *,
    name: str,
    value: Callable[[np.ndarray, int], Optional[Union[int, float]]],
    dtype: np.dtype,
    encoder: Callable[[np.ndarray], BinaryCIFEncoder],
    presence: Optional[Callable[[np.ndarray, int], Optional[ValuePresenceEnum]]] = None,
) -> FieldDesc:
    return number_field(name=name, value=value, dtype=dtype, encoder=encoder, presence=presence)


class Fields_SegmentationDataTable:
    def _value(self, table: np.ndarray, index: int):
        return table[index]

    def __init__(self, encoder: BinaryCIFEncoder, dtype: np.dtype):
        self.fields: list[FieldDesc] = [
            number_field_segmentation_table(name="name", value=self._value, encoder=lambda d: encoder, dtype=dtype)
        ]
