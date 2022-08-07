from typing import Union

import numpy as np
from ciftools.src.binary.encoding.data_types import DataType
from ciftools.src.binary.encoding.encodings import (
    ByteArrayEncoding,
    DeltaEncoding,
    FixedPointEncoding,
    IntegerPackingEncoding,
    IntervalQuantizationEncoding,
    RunLengthEncoding,
    StringArrayEncoding,
)
from ciftools.src.binary.encoding.types import EncodedCIFColumn, EncodedCIFData
from ciftools.src.cif_format.base import CIFColumnBase
from ciftools.src.cif_format.binary.column import BinaryCIFColumn


def decode_cif_column(column: EncodedCIFColumn) -> CIFColumnBase:
    values = decode_cif_data(column["data"])
    value_kinds = decode_cif_data(column["mask"]) if column["mask"] else None  # type: ignore
    return BinaryCIFColumn(column["name"], values, value_kinds)  # type: ignore


def decode_cif_data(encoded_data: EncodedCIFData) -> Union[np.ndarray, list[str]]:
    result = encoded_data["data"]
    for encoding in encoded_data["encoding"][::-1]:
        if encoding["kind"] in _decoders:
            result = _decoders[encoding["kind"]](result, encoding)  # type: ignore
        else:
            raise ValueError(f"Unsupported encoding '{encoding['kind']}'")

    return result


def _decode_byte_array(data: bytes, encoding: ByteArrayEncoding) -> np.ndarray:
    return np.frombuffer(data, dtype="<" + DataType.to_dtype(encoding["type"]))


def _decode_fixed_point(data: np.ndarray, encoding: FixedPointEncoding) -> np.ndarray:
    return np.array(data, dtype=DataType.to_dtype(encoding["srcType"])) / encoding["factor"]


def _decode_interval_quantization(data: np.ndarray, encoding: IntervalQuantizationEncoding) -> np.ndarray:
    delta = (encoding["max"] - encoding["min"]) / (encoding["numSteps"] - 1)
    return np.array(data, dtype=DataType.to_dtype(encoding["srcType"])) * delta + encoding["min"]


def _decode_run_length(data: np.ndarray, encoding: RunLengthEncoding) -> np.ndarray:
    return np.repeat(np.array(data[::2], dtype=DataType.to_dtype(encoding["srcType"])), repeats=data[1::2])


def _decode_delta(data: np.ndarray, encoding: DeltaEncoding) -> np.ndarray:
    result = np.array(data, dtype=DataType.to_dtype(encoding["srcType"]))
    if encoding["origin"]:
        result[0] += encoding["origin"]
    return np.cumsum(result, out=result)


def _decode_integer_packing_signed(data: np.ndarray, encoding: IntegerPackingEncoding) -> np.ndarray:
    upper_limit = 0x7F if encoding["byteCount"] == 1 else 0x7FFF
    lower_limit = -upper_limit - 1
    n = len(data)
    output = np.zeros(encoding["srcSize"], dtype="i4")
    i = 0
    j = 0
    while i < n:
        value = 0
        t = data[i]
        while t == upper_limit or t == lower_limit:
            value += t
            i += 1
            t = data[i]
        value += t
        output[j] = value
        i += 1
        j += 1
    return output


def _decode_integer_packing_unsigned(data: np.ndarray, encoding: IntegerPackingEncoding) -> np.ndarray:
    upper_limit = 0xFF if encoding["byteCount"] == 1 else 0xFFFF
    n = len(data)
    output = np.zeros(encoding["srcSize"], dtype="i4")
    i = 0
    j = 0
    while i < n:
        value = 0
        t = data[i]
        while t == upper_limit:
            value += t
            i += 1
            t = data[i]
        value += t
        output[j] = value
        i += 1
        j += 1
    return output


def _decode_integer_packing(data: np.ndarray, encoding: IntegerPackingEncoding) -> np.ndarray:
    if len(data) == encoding["srcSize"]:
        return data
    if encoding["isUnsigned"]:
        return _decode_integer_packing_unsigned(data, encoding)
    else:
        return _decode_integer_packing_signed(data, encoding)


def _decode_string_array(data: np.ndarray, encoding: StringArrayEncoding) -> list[str]:
    offsets = decode_cif_data(EncodedCIFData(encoding=encoding["offsetEncoding"], data=encoding["offsets"]))
    indices = decode_cif_data(EncodedCIFData(encoding=encoding["dataEncoding"], data=data))

    string_data = encoding["stringData"]
    strings = [""]

    for i in range(1, len(offsets)):
        strings.append(string_data[offsets[i - 1]: offsets[i]])  # type: ignore

    return [strings[i + 1] for i in indices]  # type: ignore


_decoders = {
    "ByteArray": _decode_byte_array,
    "FixedPoint": _decode_fixed_point,
    "IntervalQuantization": _decode_interval_quantization,
    "RunLength": _decode_run_length,
    "Delta": _decode_delta,
    "IntegerPacking": _decode_integer_packing,
    "StringArray": _decode_string_array,
}
