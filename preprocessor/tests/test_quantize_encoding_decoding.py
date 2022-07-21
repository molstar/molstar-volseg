import unittest
import dask.array as da
import numpy as np

from preprocessor.src.tools.quantize_data.quantize_data import decode_quantized_data, quantize_data

def calculate_atol(data_dict: dict):
    atol = data_dict['max'] - data_dict['min'] / data_dict['num_steps'] / 2
    if isinstance(atol, da.Array):
        return atol.compute()
    return atol

class TestEncodingsIntervalQuantization(unittest.TestCase):
    def test(self):

        test_suite = [
            (np.random.rand(100) * 100, np.uint8),
            (np.random.rand(100) * 100, np.uint16),
            (da.from_array(np.random.rand(100) * 100), np.uint8),
            (da.from_array(np.random.rand(100) * 100), np.uint16),
        ]

        for test_arr, dtype in test_suite:
            bits_in_dtype = dtype().itemsize * 8
            steps = 2**bits_in_dtype - 1
            low, high = np.min(test_arr), np.max(test_arr)
            encoded = quantize_data(data=test_arr, output_dtype=dtype)
            decoded = decode_quantized_data(encoded)
            
            atol = calculate_atol(encoded)
            self.assertTrue(np.allclose(test_arr, decoded, atol=atol),
                msg=f'{test_arr}, {decoded}')
