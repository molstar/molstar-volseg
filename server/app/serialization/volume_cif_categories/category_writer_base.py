from abc import abstractmethod
from typing import Generic, TypeVar

from ciftools.writer.base import CategoryWriter, CategoryWriterProvider, FieldDesc  # type: ignore
from ciftools.binary.encoding.impl.binary_cif_encoder import BinaryCIFEncoder  # type: ignore
from ciftools.binary.encoding.impl.encoders.byte_array import ByteArrayCIFEncoder  # type: ignore
from ciftools.binary.encoding.data_types import DataType, DataTypeEnum  # type: ignore

from app.serialization.volume_cif_categories.common import CategoryDesc, CategoryDescImpl  # type: ignore


TData = TypeVar('TData')


INT_32 = DataType.to_dtype(DataTypeEnum.Int32)
UINT_32 = DataType.to_dtype(DataTypeEnum.Int32)
FLOAT_32 = DataType.to_dtype(DataTypeEnum.Float32)


class CategoryWriterBase(CategoryWriter, Generic[TData]):
    def __init__(self, data: TData, count: int, category_desc: CategoryDesc):
        self.data = data
        self.count = count
        self.desc = category_desc


class CategoryWriterProviderBase(CategoryWriterProvider, Generic[TData]):
    @property
    @abstractmethod
    def category_name(cls) -> str:
        pass

    @abstractmethod
    def get_row_count(self, ctx: TData) -> int:
        pass

    @abstractmethod
    def get_field_desc(self, ctx: TData) -> list[FieldDesc]:
        pass

    def category_writer(self, data: TData) -> CategoryWriterBase[TData]:
        n_rows = self.get_row_count(data)
        field_desc: list[FieldDesc] = self.get_field_desc(data)
        return CategoryWriterBase(data, n_rows, CategoryDescImpl(self.category_name, field_desc))
    

def byte_array_encoder(_) -> BinaryCIFEncoder:
    return BinaryCIFEncoder([ByteArrayCIFEncoder()])
  