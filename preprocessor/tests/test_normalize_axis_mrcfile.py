import unittest
import dask.array as da
import numpy as np
from preprocessor.src.preprocessors.implementations.sff.preprocessor._volume_map_methods import normalize_axis_order_mrcfile

class TestAxisOrderNormalization(unittest.TestCase):
    def test(self):
        header_321 = type('some_object', (object,), {'mapc': 3, 'mapr': 2, 'maps': 1})()
        data_321 = np.array([[[1],[2]],[[3],[4]],[[5],[6]]])

        test_suite = [
            (da.from_array(data_321), header_321)
        ]

        for data, header in test_suite:
            normalized = normalize_axis_order_mrcfile(data, header)
            normalized = normalized.compute()

            self.assertTrue(normalized.shape == (1, 2, 3))
            

