from typing import Any, List, Optional

import msgpack
import numpy as np
from ciftools.src.binary.encoding.impl.binary_cif_encoder import BinaryCIFEncoder
from ciftools.src.binary.encoding.impl.encoders.byte_array import BYTE_ARRAY_CIF_ENCODER
from ciftools.src.binary.encoding.impl.encoders.run_length import RUN_LENGTH_CIF_ENCODER
from ciftools.src.binary.encoding.types import (
    EncodedCIFCategory,
    EncodedCIFColumn,
    EncodedCIFData,
    EncodedCIFDataBlock,
    EncodedCIFFile,
)
from ciftools.src.cif_format.value_presence import ValuePresenceEnum
from ciftools.src.writer.base import CategoryWriter, CategoryWriterProvider, CIFWriter, FieldDesc, OutputStream


class _ContextData:
    data: any
    count: int

    def __init__(self, data: any, count: int):
        self.data = data
        self.count = count


_RLE_ENCODER = BinaryCIFEncoder([RUN_LENGTH_CIF_ENCODER, BYTE_ARRAY_CIF_ENCODER])
_BYTE_ARRAY_ENCODER = BinaryCIFEncoder([BYTE_ARRAY_CIF_ENCODER])


def _always_present(data, i):
    return ValuePresenceEnum.Present


class BinaryCIFWriter(CIFWriter):

    _data: Optional[EncodedCIFFile]
    _data_blocks: list[EncodedCIFDataBlock]
    _encoded_data: np.ndarray  # bytes -> uint8

    def __init__(self, encoder: str):
        self._data_blocks = []
        self._data = {"version": "0.3.0", "encoder": encoder, "dataBlocks": self._data_blocks}

    def start_data_block(self, header: str) -> None:
        # TODO: optimize if needed
        _header = header.replace(" ", "").replace("\n", "").replace("\t", "").upper()
        self._data_blocks.append({"header": _header, "categories": []})

    def write_category(self, writer_provider: CategoryWriterProvider, contexts: List[Any]) -> None:

        if not self._data:
            raise Exception("The writer contents have already been encoded, no more writing.")

        if not self._data_blocks:
            raise Exception("No data block created.")

        if not contexts:
            src = [writer_provider.category_writer(None)]
        else:
            src = [writer_provider.category_writer(ctx) for ctx in contexts]

        categories: list[CategoryWriter] = list(filter(lambda writer: writer.count > 0, src))
        if not categories:
            return

        count = 0
        for cat in categories:
            count += cat.count
        if not count:
            return

        first = categories[0]
        cif_cat: EncodedCIFCategory = {"name": f"_{first.desc.name}", "rowCount": count, "columns": []}
        data = [_ContextData(c.data, c.count) for c in categories]

        for f in first.desc.fields:
            cif_cat["columns"].append(BinaryCIFWriter._encode_field(f, data, count))

        self._data_blocks[len(self._data_blocks) - 1]["categories"].append(cif_cat)

    def encode(self) -> None:
        self._encoded_data = msgpack.dumps(self._data)
        self._data = None
        self._data_blocks = []

    def flush(self, stream: OutputStream) -> None:
        stream.write_binary(self._encoded_data)

    @staticmethod
    def _encode_field(field: FieldDesc, data: list[_ContextData], total_count: int) -> EncodedCIFColumn:
        array: np.ndarray
        array = field.create_array(total_count)
        is_native: bool = not hasattr(array, "dtype")

        mask = np.ndarray(shape=[total_count], dtype=np.dtype(np.uint8))
        presence = field.presence or _always_present
        all_present = True

        offset = 0
        for _d in data:
            d = _d.data
            for i in range(_d.count):
                p = presence(d, i)
                if p is not ValuePresenceEnum.Present:
                    mask[offset] = p
                    if is_native:
                        array[offset] = None
                    all_present = False
                else:
                    mask[offset] = ValuePresenceEnum.Present
                    array[offset] = field.value(d, i)

                offset += 1

        encoder = field.encoder(data[0].data) if len(data) > 0 else _BYTE_ARRAY_ENCODER
        encoded = encoder.encode_cif_data(array)

        mask_data: Optional[EncodedCIFData] = None

        if not all_present:
            mask_rle = _RLE_ENCODER.encode_cif_data(mask)
            if len(mask_rle["data"]) < len(mask):
                mask_data = mask_rle
            else:
                mask_data = _BYTE_ARRAY_ENCODER.encode_cif_data(mask)

        return {"name": field.name, "data": encoded, "mask": mask_data}
