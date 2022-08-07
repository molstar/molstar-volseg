from typing import Union

import numpy as np
from ciftools.src.binary.encoding.impl.binary_cif_encoder import BinaryCIFEncoder
from ciftools.src.binary.encoding.base.cif_encoder_base import CIFEncoderBase
from ciftools.src.binary.encoding.encodings import EncodingEnun, StringArrayEncoding
from ciftools.src.binary.encoding.impl.encoders.delta import DELTA_CIF_ENCODER
from ciftools.src.binary.encoding.impl.encoders.integer_packing import INTEGER_PACKING_CIF_ENCODER
from ciftools.src.binary.encoding.impl.encoders.run_length import RUN_LENGTH_CIF_ENCODER
from ciftools.src.binary.encoding.types import EncodedCIFData

# TODO: use classifier once implemented
_OFFSET_ENCODER = BinaryCIFEncoder([DELTA_CIF_ENCODER, INTEGER_PACKING_CIF_ENCODER])
_DATA_ENCODER = BinaryCIFEncoder([DELTA_CIF_ENCODER, RUN_LENGTH_CIF_ENCODER, INTEGER_PACKING_CIF_ENCODER])


class StringArrayCIFEncoder(CIFEncoderBase):
    def encode(self, data: Union[np.ndarray, list[str]]) -> EncodedCIFData:
        _map = dict()

        strings: list[str] = []
        offsets = [0]
        output = np.empty(len(data), dtype="i4")

        acc_len = 0

        for i, s in enumerate(data):
            # handle null strings.
            if not s:
                output[i] = -1
                continue

            index = _map.get(s)
            if index is None:
                # increment the length
                acc_len += len(s)

                # store the string and index
                index = len(strings)
                strings.append(s)
                _map[s] = index

                # write the offset
                offsets.append(acc_len)

            output[i] = index

        encoded_offsets = _OFFSET_ENCODER.encode_cif_data(np.array(offsets, dtype="i4"))
        encoded_data = _DATA_ENCODER.encode_cif_data(output)

        encoding: StringArrayEncoding = {
            "dataEncoding": encoded_data["encoding"],
            "kind": EncodingEnun.StringArray,
            "stringData": "".join(strings),
            "offsetEncoding": encoded_offsets["encoding"],
            "offsets": encoded_offsets["data"],
        }

        return EncodedCIFData(data=encoded_data["data"], encoding=[encoding])


STRING_ARRAY_CIF_ENCODER = StringArrayCIFEncoder()
