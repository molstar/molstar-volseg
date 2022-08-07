import unittest

import msgpack
import numpy as np
from ciftools.src.binary.decoder import decode_cif_data
from ciftools.src.binary.encoding.impl.binary_cif_encoder import BinaryCIFEncoder
from ciftools.src.binary.encoding.impl.encoders.byte_array import BYTE_ARRAY_CIF_ENCODER
from ciftools.src.binary.encoding.impl.encoders.delta import DELTA_CIF_ENCODER
from ciftools.src.binary.encoding.impl.encoders.fixed_point import FixedPointCIFEncoder


class TestEncodings_FixedPoint(unittest.TestCase):
    def test(self):

        test_suite = [
            (np.random.rand(100) * 1000, 1),
            (np.random.rand(100) * 1000, 2),
            (np.random.rand(100) * 1000, 3),
            (np.random.rand(100) * 1000, 4),
        ]

        for test_arr, e in test_suite:
            encoder = BinaryCIFEncoder([FixedPointCIFEncoder(10 ** e), BYTE_ARRAY_CIF_ENCODER])
            encoded = encoder.encode_cif_data(test_arr)
            decoded = decode_cif_data(encoded)

            self.assertTrue(np.allclose(test_arr, decoded, atol=10 ** (-e)))


class TestEncodings_FixedPointDelta(unittest.TestCase):
    def test(self):

        test_suite = [
            (np.random.rand(100) * 1000, 1),
            (np.random.rand(100) * 1000, 2),
            (np.random.rand(100) * 1000, 3),
            (np.random.rand(100) * 1000, 4),
            (np.array([24.41149862, 93.41400854, 25.07853073, 86.43384453, 73.12187345], dtype="f4"), 3),
        ]

        for test_arr, e in test_suite:
            encoder = BinaryCIFEncoder([
                FixedPointCIFEncoder(10 ** e), DELTA_CIF_ENCODER, BYTE_ARRAY_CIF_ENCODER
            ])
            encoded = encoder.encode_cif_data(test_arr)
            msgpack.loads(msgpack.dumps(encoded))
            decoded = decode_cif_data(encoded)

            self.assertTrue(np.allclose(test_arr, decoded, atol=10 ** (-e)))
