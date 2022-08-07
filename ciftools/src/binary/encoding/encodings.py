from enum import Enum
from typing import TypedDict

import numpy as np


class EncodingEnun(str, Enum):
    ByteArray = "ByteArray"
    FixedPoint = "FixedPoint"
    RunLength = "RunLength"
    Delta = "Delta"
    IntervalQuantization = "IntervalQuantization"
    IntegerPacking = "IntegerPacking"
    StringArray = "StringArray"


class EncodingBase(TypedDict):
    kind: EncodingEnun


# type[] -> Uint8[]
class ByteArrayEncoding(EncodingBase):
    type: int


# (Float32 | Float64)[] -> Int32[]
class FixedPointEncoding(EncodingBase):
    factor: float
    srcType: int


#  (Float32|Float64)[] -> Int32
class IntervalQuantizationEncoding(EncodingBase):
    min: float
    max: float
    numSteps: int
    srcType: int


#  (Uint8 | Int8 | Int16 | Int32)[] -> Int32[]
class RunLengthEncoding(EncodingBase):
    srcType: int
    srcSize: int


#  T=(Int8Array | Int16Array | Int32Array)[] -> T[]
class DeltaEncoding(EncodingBase):
    origin: int
    srcType: int


# Int32[] -> (Int8 | Int16 | Uint8 | Uint16)[]
class IntegerPackingEncoding(EncodingBase):
    byteCount: int
    isUnsigned: bool
    srcSize: int


# string[] -> Uint8[]
# stores 0 and indices of ends of strings:
# stringData = '123456'
# offsets = [0,2,5,6]
# encodes ['12','345','6']
class StringArrayEncoding(EncodingBase):
    dataEncoding: list[EncodingBase]
    stringData: str
    offsetEncoding: list[EncodingBase]
    offsets: np.ndarray
