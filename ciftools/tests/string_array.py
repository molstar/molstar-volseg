import unittest

import msgpack
import numpy as np
from ciftools.src.binary.decoder import decode_cif_data
from ciftools.src.binary.encoding.impl.binary_cif_encoder import BinaryCIFEncoder
from ciftools.src.binary.encoding.impl.encoders.string_array import STRING_ARRAY_CIF_ENCODER


class TestEncodings_StringArray(unittest.TestCase):
    def test(self):
        test_arr = [
            "my",
            "cat",
            "eats",
            "too",
            "much",
            "food",
            "off",
            "my",
            "my",
            "",
            "plate",
            "because",
            "",
            "my",
            "cat",
        ]

        encoder = BinaryCIFEncoder([STRING_ARRAY_CIF_ENCODER])
        encoded = encoder.encode_cif_data(test_arr)
        msgpack.loads(msgpack.dumps(encoded))
        decoded = decode_cif_data(encoded)

        self.assertTrue(np.array_equal(test_arr, decoded))
