from ciftools.writer.base import CategoryWriter, CategoryWriterProvider


class CategoryWriterProvider_SegmentationLattice(CategoryWriterProvider):
    length: int

    def __init__(self, length: int):
        self.length = length

    def category_writer(self, ctx: any) -> CategoryWriter:
        pass
