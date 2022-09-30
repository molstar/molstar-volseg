from abc import abstractmethod
from typing import Generic, TypeVar

from ciftools.writer.base import CategoryDesc, FieldDesc, CategoryWriter, CategoryWriterProvider
from db.interface.i_preprocessed_medatada import IPreprocessedMetadata

from app.core.models import GridSliceBox


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
        field_desc: list[FieldDesc] = self.get_field_descriptors(data)
        return CategoryWriterBase(data, n_rows, CategoryDescImpl(self.category_name, field_desc))
    

class VolumeInfo:
    def __init__(
        self,
        name: str,
        metadata: IPreprocessedMetadata,
        box: GridSliceBox,
    ):
        self.name = name
        self.metadata = metadata
        self.box = box

        self.grid_size = box.dimensions

        downsampling_rate = box.downsampling_rate
        voxel_size = metadata.voxel_size(downsampling_rate)
        full_grid_size = metadata.sampled_grid_dimensions(downsampling_rate)

        cartn_origin = metadata.origin()

        self.cell_size = [voxel_size[i] * full_grid_size[i] for i in range(3)]
        self.origin = [cartn_origin[i] / self.cell_size[i] for i in range(3)]
        self.dimensions = [self.grid_size[i] * voxel_size[i] / self.cell_size[i] for i in range(3)]
