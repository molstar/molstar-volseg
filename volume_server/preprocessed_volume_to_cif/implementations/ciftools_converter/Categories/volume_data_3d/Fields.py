from typing import Callable, Optional

import numpy as np
from ciftools.binary.encoding import BinaryCIFEncoder
from ciftools.cif_format import ValuePresenceEnum
from ciftools.writer.base import FieldDesc
from ciftools.writer.fields import number_field

from db.interface.i_preprocessed_volume import IPreprocessedVolume


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
        self.fields: list[FieldDesc] = [
            number_field_volume3d(name="name", value=self._value, encoder=lambda d: encoder, dtype=dtype)
        ]