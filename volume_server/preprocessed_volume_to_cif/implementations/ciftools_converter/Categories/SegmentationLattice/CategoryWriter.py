from ciftools.Writer.CategoryWriter import CategoryWriter
from ciftools.Writer.CategoryWriterProvider import CategoryWriterProvider


class CategoryWriterProvider_SegmentationLattice(CategoryWriterProvider):
    length: int

    def __init__(self, length: int):
        self.length = length

    def category_writer(self, ctx: any) -> CategoryWriter:
        pass
