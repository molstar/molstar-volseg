from ciftools.Writer.CategoryWriter import CategoryWriter
from ciftools.Writer.CategoryWriterProvider import CategoryWriterProvider
from ciftools.Writer.FieldDesc import FieldDesc

from db.interface.i_preprocessed_medatada import IPreprocessedMetadata
from volume_server.preprocessed_volume_to_cif.implementations.ciftools_converter.Categories._writer import \
    CategoryDesc
from volume_server.preprocessed_volume_to_cif.implementations.ciftools_converter.Categories.Metadata.Fields.lattice_ids import \
    FieldDesc_LatticeIds


class CategoryWriter_IPreprocessedMetadata(CategoryWriter):
    def __init__(self, data: IPreprocessedMetadata, count: int, category_desc: CategoryDesc):
        self.data = data
        self.count = count
        self.desc = category_desc


class CategoryWriterProvider_Metadata(CategoryWriterProvider):
    def category_writer(self, ctx: IPreprocessedMetadata) -> CategoryWriter:
        field_desc: list[FieldDesc] = [FieldDesc_LatticeIds()]  # TODO: add all fields
        return CategoryWriter_IPreprocessedMetadata(ctx, 1, CategoryDesc("metadata", field_desc))  # TODO: handle len
