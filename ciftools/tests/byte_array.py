import unittest

import msgpack
import numpy as np
from ciftools.src.binary.decoder import decode_cif_data
from ciftools.src.binary.encoding.impl.binary_cif_encoder import BinaryCIFEncoder
from ciftools.src.binary.encoding.data_types import DataTypeEnum
from ciftools.src.binary.encoding.impl.encoders.byte_array import BYTE_ARRAY_CIF_ENCODER


# noinspection PyTypedDict
class TestEncodings_ByteArray(unittest.TestCase):
    def test(self):
        test_suite = [
            (np.array(np.random.rand(100) * 100, dtype="i1"), DataTypeEnum.Int8),
            (np.array(np.random.rand(100) * 100, dtype="u1"), DataTypeEnum.Uint8),
            (np.array(np.random.rand(100) * 100, dtype="b"), DataTypeEnum.Int8),
            (np.array(np.random.rand(100) * 100, dtype="B"), DataTypeEnum.Uint8),
            (np.array(np.random.rand(100) * 100, dtype="i2"), DataTypeEnum.Int16),
            (np.array(np.random.rand(100) * 100, dtype="u2"), DataTypeEnum.Uint16),
            (np.array(np.random.rand(100) * 100, dtype=">i2"), DataTypeEnum.Int16),
            (np.array(np.random.rand(100) * 100, dtype=">u2"), DataTypeEnum.Uint16),
            (np.array(np.random.rand(100) * 100, dtype="i4"), DataTypeEnum.Int32),
            (np.array(np.random.rand(100) * 100, dtype="u4"), DataTypeEnum.Uint32),
            (np.array(np.random.rand(100) * 100, dtype=">i4"), DataTypeEnum.Int32),
            (np.array(np.random.rand(100) * 100, dtype=">u4"), DataTypeEnum.Uint32),
            (np.array(np.random.rand(100) * 100, dtype="f4"), DataTypeEnum.Float32),
            (np.array(np.random.rand(100) * 100, dtype="f8"), DataTypeEnum.Float64),
            (np.array(np.random.rand(100) * 100, dtype=">f4"), DataTypeEnum.Float32),
            (np.array(np.random.rand(100) * 100, dtype=">f8"), DataTypeEnum.Float64),
        ]

        for test_arr, expected_type in test_suite:
            encoder = BinaryCIFEncoder([BYTE_ARRAY_CIF_ENCODER])
            encoded = encoder.encode_cif_data(test_arr)

            msgpack.loads(msgpack.dumps(encoded))

            decoded = decode_cif_data(encoded)

            self.assertTrue(np.array_equal(test_arr, decoded))
            self.assertEqual(encoded["encoding"][0]["type"], expected_type)
