from typing import Union

import msgpack
from ciftools.src.cif_format.base import CIFDataBlockBase, CIFFileBase
from ciftools.src.cif_format.binary.category import BinaryCIFCategory
from ciftools.src.cif_format.binary.data_block import BinaryCIFDataBlock


class BinaryCIFFile(CIFFileBase):
    def __getitem__(self, index_or_name: Union[int, str]):
        """
        Access a data block by index or header (case sensitive)
        """
        if isinstance(index_or_name, str):
            return self._block_map[index_or_name] if index_or_name in self._block_map else None
        else:
            return self.data_blocks[index_or_name] if index_or_name < len(self.data_blocks) else None

    def __len__(self):
        return len(self.data_blocks)

    def __contains__(self, key: str):
        return key in self._block_map

    def __init__(self, data_blocks: list[BinaryCIFDataBlock]):
        self.data_blocks = data_blocks
        self._block_map: dict[str, CIFDataBlockBase] = {b.header: b for b in data_blocks}

    @staticmethod
    def loads(data: Union[bytes, dict], lazy=True) -> "BinaryCIFFile":
        """
        - data: msgpack encoded blob or EncodedFile object
        - lazy:
            - True: individual columns are decoded only when accessed
            - False: decode all columns immediately
        """

        file: dict = data if isinstance(data, dict) and "dataBlocks" in data else msgpack.loads(data)  # type: ignore

        data_blocks = [
            BinaryCIFDataBlock(
                block["header"],
                {category["name"][1:]: BinaryCIFCategory(category, lazy) for category in block["categories"]},
            )
            for block in file["dataBlocks"]
        ]

        return BinaryCIFFile(data_blocks)

    def data_blocks(self) -> list[CIFDataBlockBase]:
        return list(self._block_map.values())

    def data_block(self, name: str) -> Union[CIFDataBlockBase, None]:
        return self._block_map.get(name, None)
