import unittest
import dask.array as da
import numpy as np

from preprocessor.src.tools.quantize_data.quantize_data import decode_quantized_data, quantize_data

class TestEncodingsIntervalQuantization(unittest.TestCase):
    def test(self):

        test_suite = [
            (np.random.rand(100) * 100, np.uint8),
            (np.random.rand(100) * 100, np.uint16),
            (np.random.rand(100) * 100, np.int8),
            (np.random.rand(100) * 100, np.int16),
            (da.from_array(np.random.rand(100) * 100), np.uint8),
            (da.from_array(np.random.rand(100) * 100), np.uint16),
            (da.from_array(np.random.rand(100) * 100), np.int8),
            (da.from_array(np.random.rand(100) * 100), np.int16),
        ]

        for test_arr, dtype in test_suite:
            bits_in_dtype = dtype().itemsize * 8
            steps = 2**bits_in_dtype - 1
            low, high = np.min(test_arr), np.max(test_arr)
            encoded = quantize_data(data=test_arr, output_dtype=dtype)
            decoded = decode_quantized_data(encoded)
            
            self.assertTrue(np.allclose(test_arr, decoded, atol=1.1 * (high - low) / steps),
                msg=f'{test_arr}, {decoded}')
