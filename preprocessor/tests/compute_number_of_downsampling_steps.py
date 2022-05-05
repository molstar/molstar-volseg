import unittest

import numpy as np

from preprocessor.implementations.sff_preprocessor import MIN_GRID_SIZE, SFFPreprocessor


class TestComputeNumberOfDownsamplingSteps(unittest.TestCase):
    def test(self):
        #input grid size, dtype, 
        # TODO: provide expected output values
        test_suite = [
            (100**3, np.uint8, ),
            (1000**3, np.float32, ),
            (20**3, np.float32, ),
            (100**3, np.float32, )
        ]

        p = SFFPreprocessor()

        for input_grid_size, grid_dtype, expected_nsteps in test_suite:
            number_of_downsampling_steps = p.__compute_number_of_downsampling_steps(
                MIN_GRID_SIZE,
                input_grid_size,
                force_dtype=grid_dtype
                )

            self.assertEqual(number_of_downsampling_steps, expected_nsteps)

