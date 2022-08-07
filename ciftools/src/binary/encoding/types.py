from typing import Optional, TypedDict

from ciftools.src.binary.encoding.encodings import EncodingBase


class EncodedCIFData(TypedDict):
    encoding: list[EncodingBase]
    data: bytes


class EncodedCIFColumn(TypedDict):
    name: str
    data: EncodedCIFData
    mask: Optional[EncodedCIFData]


class EncodedCIFCategory(TypedDict):
    name: str
    rowCount: int
    columns: list[EncodedCIFColumn]


class EncodedCIFDataBlock(TypedDict):
    header: str
    categories: list[EncodedCIFCategory]


class EncodedCIFFile(TypedDict):
    version: str
    encoder: str
    dataBlocks: list[EncodedCIFDataBlock]
