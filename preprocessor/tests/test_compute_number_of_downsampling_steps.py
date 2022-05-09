import unittest

import numpy as np

from preprocessor.src.preprocessors.implementations.sff.preprocessor.downsampling_methods import compute_number_of_downsampling_steps
from preprocessor.src.preprocessors.implementations.sff.preprocessor.sff_preprocessor import MIN_GRID_SIZE

class TestComputeNumberOfDownsamplingSteps(unittest.TestCase):
    def test(self):
        #input grid size, dtype, expected nsteps
        downsampling_factor = 2**3
        test_suite = [
            (120**3, np.uint8, 1),
            (1000**3, np.uint8, 2),
            (1000**3, np.float32, 3),
            (20**3, np.float32, 1),
            (120**3, np.float32, 1)
        ]

        for input_grid_size, grid_dtype, expected_nsteps in test_suite:
            number_of_downsampling_steps = compute_number_of_downsampling_steps(
                MIN_GRID_SIZE,
                input_grid_size,
                force_dtype=grid_dtype,
                factor=downsampling_factor,
                min_downsampled_file_size_bytes=5*10**6
                )

            self.assertEqual(number_of_downsampling_steps, expected_nsteps, f'Test suite: {input_grid_size}, {grid_dtype}, {expected_nsteps}')
            filesize_of_original_file = input_grid_size * grid_dtype().itemsize / 1000000
            filesize_of_last_downsampling = filesize_of_original_file / (downsampling_factor**number_of_downsampling_steps)
            print(f'Original filesize: {filesize_of_original_file} MB, last downsampling filesize: {filesize_of_last_downsampling} MB')