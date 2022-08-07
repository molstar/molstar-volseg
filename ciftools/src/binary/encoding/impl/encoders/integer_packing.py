import math

import numpy as np
from ciftools.src.binary.encoding.base.cif_encoder_base import CIFEncoderBase
from ciftools.src.binary.encoding.encodings import EncodingEnun, IntegerPackingEncoding
from ciftools.src.binary.encoding.impl.encoders.byte_array import BYTE_ARRAY_CIF_ENCODER
from ciftools.src.binary.encoding.types import EncodedCIFData
from numpy import int8, int16, uint8, uint16


class IntegerPackingCIFEncoder(CIFEncoderBase):
    def encode(self, data: np.ndarray) -> EncodedCIFData:

        # TODO: must be 32bit integer

        packing = _determine_packing(data)
        if packing.bytesPerElement == 4:
            return BYTE_ARRAY_CIF_ENCODER.encode(data)

        # integer packing

        if packing.isSigned:
            if packing.bytesPerElement == 1:
                upper_limit = 0x7F
                packed = np.empty(packing.size, dtype=int8)
            else:
                upper_limit = 0x7FFF
                packed = np.empty(packing.size, dtype=int16)
        else:
            if packing.bytesPerElement == 1:
                upper_limit = 0xFF
                packed = np.empty(packing.size, dtype=uint8)
            else:
                upper_limit = 0xFFFF
                packed = np.empty(packing.size, dtype=uint16)

        lower_limit = -upper_limit - 1

        # TODO: figure out if there is a way to implement this
        # better & faster with numpy methods.
        packed_index = 0
        for _v in data:
            value = _v
            if value >= 0:
                while value >= upper_limit:
                    packed[packed_index] = upper_limit
                    packed_index += 1
                    value -= upper_limit
            else:
                while value <= lower_limit:
                    packed[packed_index] = lower_limit
                    packed_index += 1
                    value -= lower_limit

            packed[packed_index] = value
            packed_index += 1

        byte_array_result = BYTE_ARRAY_CIF_ENCODER.encode(packed)

        integer_packing_encoding: IntegerPackingEncoding = {
            "kind": EncodingEnun.IntegerPacking,
            "isUnsigned": not packing.isSigned,
            "srcSize": len(data),
            "byteCount": packing.bytesPerElement,
        }

        return EncodedCIFData(
            data=byte_array_result["data"], encoding=[integer_packing_encoding, byte_array_result["encoding"][0]]
        )


class _PackingInfo:
    isSigned: bool
    size: int
    bytesPerElement: int


def _determine_packing(data: np.ndarray) -> _PackingInfo:
    # determine sign
    is_signed = np.any(data < 0)

    # determine packing size
    size8 = _packing_size(data, 0x7F) if is_signed else _packing_size(data, 0xFF)
    size16 = _packing_size(data, 0x7FFF) if is_signed else _packing_size(data, 0xFFFF)

    packing = _PackingInfo()
    packing.isSigned = is_signed

    data_len = len(data)

    if data_len * 4 < size16 * 2:
        packing.size = data_len
        packing.bytesPerElement = 4

    elif size16 * 2 < size8:
        packing.size = size16
        packing.bytesPerElement = 2

    else:
        packing.size = size8
        packing.bytesPerElement = 1

    return packing


def _packing_size(data: np.ndarray, upper_limit: int) -> int:
    lower_limit = -upper_limit - 1
    size = 0

    for value in data:
        if value == 0:
            size = size + 1
        elif value > 0:
            size = size + math.ceil(value / upper_limit)
            if value % upper_limit == 0:
                size = size + 1
        else:
            size = size + math.ceil(value / lower_limit)
            if value % lower_limit == 0:
                size = size + 1

    return size


INTEGER_PACKING_CIF_ENCODER = IntegerPackingCIFEncoder()
