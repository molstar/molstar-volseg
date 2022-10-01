from abc import abstractmethod
from typing import Generic, TypeVar

from ciftools.writer.base import CategoryDesc, FieldDesc, CategoryWriter, CategoryWriterProvider


TData = TypeVar('TData')


# TODO: Update CategoryDesc in CifTools to a dataclass
class CategoryDescImpl(CategoryDesc):
    def __init__(self, name: str, fields: list[FieldDesc]):
        self.name = name
        self.fields = fields


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
    def get_field_descriptors(self, ctx: TData) -> list[FieldDesc]:
        pass

    def category_writer(self, data: TData) -> CategoryWriterBase[TData]:
        n_rows = self.get_row_count(data)
        field_desc = self.get_field_descriptors(data)
        return CategoryWriterBase(data, n_rows, CategoryDescImpl(self.category_name, field_desc))
    
