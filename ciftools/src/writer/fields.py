from typing import Any, Callable, Optional, Union

import numpy as np
from ciftools.src.binary.encoding.impl.binary_cif_encoder import BinaryCIFEncoder
from ciftools.src.binary.encoding.impl.encoders.string_array import STRING_ARRAY_CIF_ENCODER
from ciftools.src.cif_format.value_presence import ValuePresenceEnum
from ciftools.src.writer.base import FieldDesc

_STRING_ARRAY_ENCODER = BinaryCIFEncoder([STRING_ARRAY_CIF_ENCODER])


# TODO: derive from FieldDesc
class _StringFieldDesc(FieldDesc):
    def value(self, data: Any, i: int) -> Any:
        return self._value(data, i)

    def presence(self, data: any, i: int) -> ValuePresenceEnum:
        return self.presence(data, i) if self._presence else ValuePresenceEnum.Present

    def create_array(self, total_count: int):
        return [""] * total_count

    def encoder(self, data: Any):
        return _STRING_ARRAY_ENCODER

    def __init__(
        self,
        name: str,
        value: Callable[[Any, int], Optional[str]],
        presence: Optional[Callable[[Any, int], Optional[ValuePresenceEnum]]] = None,
    ) -> None:
        self.name = name
        self._value = value
        self._presence = presence


def string_field(
    *,
    name: str,
    value: Callable[[Any, int], Optional[str]],
    presence: Optional[Callable[[Any, int], Optional[ValuePresenceEnum]]] = None,
) -> FieldDesc:
    return _StringFieldDesc(name=name, value=value, presence=presence)


# TODO: derive from FieldDesc
class _NumberFieldDesc(FieldDesc):
    def value(self, data: Any, i: int) -> Any:
        return self._value(data, i)

    def encoder(self, data: Any) -> BinaryCIFEncoder:
        return self._encoder(data)

    def presence(self, data: any, i: int) -> ValuePresenceEnum:
        return self.presence(data, i) if self._presence else ValuePresenceEnum.Present

    def create_array(self, total_count: int):
        return np.empty(total_count, dtype=self._dtype)

    def __init__(
        self,
        name: str,
        value: Callable[[Any, int], Optional[Union[int, float]]],
        dtype: np.dtype,
        encoder: Callable[[Any], BinaryCIFEncoder],
        presence: Optional[Callable[[Any, int], Optional[ValuePresenceEnum]]] = None,
    ) -> None:
        self.name = name
        self._value = value
        self._dtype = dtype
        self._encoder = encoder
        self._presence = presence


def number_field(
    *,
    name: str,
    value: Callable[[Any, int], Optional[Union[int, float]]],
    dtype: np.dtype,
    encoder: Callable[[Any], BinaryCIFEncoder],
    presence: Optional[Callable[[Any, int], Optional[ValuePresenceEnum]]] = None,
) -> FieldDesc:
    return _NumberFieldDesc(name=name, value=value, dtype=dtype, encoder=encoder, presence=presence)
