from typing import Union
import unittest
import dask.array as da
import numpy as np

from preprocessor.src.tools.quantize_data.quantize_data import decode_quantized_data, quantize_data

def calculate_atol(data_dict: dict):
    atol = (data_dict['max'] - data_dict['min']) / data_dict['num_steps'] / 2
    if isinstance(atol, da.Array):
        return atol.compute()
    return atol

def transform_data_to_log_space(data: Union[da.Array, np.ndarray]) -> Union[da.Array, np.ndarray]:
    original_min = data.min()
    to_remove_negatives = original_min - 1

    # remove negatives
    da.subtract(data, to_remove_negatives, out=data)
    # log transform
    data = da.log(data)

    if isinstance(data, da.Array):
        data = data.compute()

    return data

class TestEncodingsIntervalQuantization(unittest.TestCase):
    def test(self):

        test_suite = [
            (np.random.rand(100) * 100, np.uint8),
            (np.random.rand(100) * 100, np.uint16),
            (da.from_array(np.random.rand(100) * 100), np.uint8),
            (da.from_array(np.random.rand(100) * 100), np.uint16),
        ]

        for test_arr, dtype in test_suite:
            encoded = quantize_data(data=test_arr, output_dtype=dtype)
            decoded = decode_quantized_data(encoded)
            
            atol = calculate_atol(encoded)
            rtol = 1e-06
            tol = 1.1 * (atol + rtol)

            decoded_log = transform_data_to_log_space(decoded)
            cmp_log = transform_data_to_log_space(test_arr)

            max_diff = da.max(da.absolute(decoded_log - cmp_log))
            if isinstance(max_diff, da.Array):
                max_diff = max_diff.compute()

            # print(tol)
            # print(max_diff)
            self.assertTrue(max_diff <= tol, msg=f'{max_diff}, {tol}')
            # self.assertTrue(np.allclose(decoded_log, cmp_log, atol=atol, rtol=rtol),
            #     msg=f'{decoded_log}, {cmp_log}')

