from enum import IntEnum
from typing import Union

import numpy as np


class DataTypeEnum(IntEnum):
    Int8 = 1
    Int16 = 2
    Int32 = 3
    Uint8 = 4
    Uint16 = 5
    Uint32 = 6
    Float32 = 32
    Float64 = 33


class DataType:
    __data_types_to_dtypes: dict[int, Union[np.dtype, str]] = {
        DataTypeEnum.Int8.value: "i1",
        DataTypeEnum.Int16.value: "i2",
        DataTypeEnum.Int32.value: "i4",
        DataTypeEnum.Uint8.value: "u1",
        DataTypeEnum.Uint16.value: "u2",
        DataTypeEnum.Uint32.value: "u4",
        DataTypeEnum.Float32.value: "f4",
        DataTypeEnum.Float64.value: "f8",
    }

    __dtypes_to_data_types: dict[Union[np.dtype, str], int] = {
        **{data_type: dtype for dtype, data_type in __data_types_to_dtypes.items()},
        "b": DataTypeEnum.Int8.value,
        "B": DataTypeEnum.Uint8.value,
    }

    @staticmethod
    def from_dtype(dtype: Union[np.dtype, str]) -> DataTypeEnum:
        t = str(dtype.str)
        if t[0] in (">", "<", "|"):
            t = t[1:]
        return DataTypeEnum(DataType.__dtypes_to_data_types[t])

    @staticmethod
    def to_dtype(data_type: Union[DataTypeEnum, int]) -> Union[np.dtype, str]:
        return DataType.__data_types_to_dtypes[int(data_type)]
