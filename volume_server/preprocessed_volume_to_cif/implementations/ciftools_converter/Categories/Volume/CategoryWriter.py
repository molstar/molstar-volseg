from ciftools.Writer.CategoryWriter import CategoryWriter
from ciftools.Writer.CategoryWriterProvider import CategoryWriterProvider

from db.interface.i_preprocessed_volume import IPreprocessedVolume
from volume_server.preprocessed_volume_to_cif.implementations.ciftools_converter.Categories._writer import CategoryDesc


class CategoryWriter_IPreprocessedMetadata(CategoryWriter):
    def __init__(self, data: IPreprocessedVolume, count: int, category_desc: CategoryDesc):
        self.data = data
        self.count = count
        self.desc = category_desc


class CategoryWriterProvider_LatticeIds(CategoryWriterProvider):
    length: int

    def __init__(self, length: int):
        self.length = length

    def category_writer(self, ctx: IPreprocessedVolume) -> CategoryWriter:
        pass
