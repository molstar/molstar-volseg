from typing import Union

from ciftools.src.cif_format.base import CIFCategoryBase, CIFDataBlockBase
from ciftools.src.cif_format.binary.category import BinaryCIFCategory


class BinaryCIFDataBlock(CIFDataBlockBase):
    def __getattr__(self, name: str) -> object:
        return self._categories[name]

    def __getitem__(self, name: str) -> BinaryCIFCategory:
        return self._categories[name]

    def __contains__(self, key: str):
        return key in self._categories

    def __init__(self, header: str, categories: dict[str, BinaryCIFCategory]):
        self.header = header
        self._categories = categories
        self._additional_data: dict[str, object] = dict()

    def header(self) -> str:
        return self._header

    def categories(self) -> dict[str, CIFCategoryBase]:
        return self._categories

    def get_category(self, name: str) -> Union[CIFCategoryBase, None]:
        return self._categories.get(name, None)

    def additional_data(self) -> dict[str, object]:
        return self._additional_data
