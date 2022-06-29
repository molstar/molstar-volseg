import json
import unittest

import requests

from volume_server.tests._test_server_runner import ServerTestBase


class FetchMetadataTest(ServerTestBase):
    def test(self):
        try:
            with self.server.run_in_thread():
                r = requests.get(f'{self.serverUrl()}/v1/emdb/emd-1832/metadata/')
                self.assertEqual(r.status_code, 200)
                body: dict = dict(r.json())
                self.assertIsNotNone(body)

                # check grid metadata
                grid_metadata = body.get("grid")
                self.assertIsNotNone(grid_metadata)
                grid_metadata: dict = dict(grid_metadata)

                # get volumes metadata
                volume_metadata = grid_metadata.get("volumes")

                # assert downsamplings start at 1 and always double
                volume_downsamplings: list = volume_metadata.get("volume_downsamplings")
                self.assertIsNotNone(volume_downsamplings)
                self.assertTrue(len(volume_downsamplings) > 0)
                previous_downsampling = volume_downsamplings[0]
                self.assertEqual(previous_downsampling, 1)
                for i in range(1, len(volume_downsamplings)):
                    self.assertEqual(volume_downsamplings[i], 2 * previous_downsampling)
                    previous_downsampling = volume_downsamplings[i]

                self.assertIsNotNone(dict())

                # get segmentation metadata
                segmentation_metadata = grid_metadata.get("segmentation_lattices")

                # assert all segmentations contain valid downsamplings
                segmentation_lattices: list = segmentation_metadata.get("segmentation_lattice_ids")
                self.assertIsNotNone(segmentation_lattices)
                self.assertTrue(len(segmentation_lattices) > 0)
                segmentation_downsamplings_dict: dict = segmentation_metadata.get("segmentation_downsamplings")
                self.assertIsNotNone(segmentation_downsamplings_dict)
                for i in range(0, len(segmentation_lattices)):
                    segmentation_downsamplings: list = segmentation_downsamplings_dict.get(
                        str(segmentation_lattices[i]))
                    self.assertIsNotNone(segmentation_downsamplings)
                    self.assertTrue(volume_downsamplings == segmentation_downsamplings)
                    previous_downsampling = segmentation_downsamplings[0]
                    self.assertEqual(previous_downsampling, 1)
                    for i in range(1, len(segmentation_downsamplings)):
                        self.assertEqual(segmentation_downsamplings[i], 2 * previous_downsampling)
                        previous_downsampling = segmentation_downsamplings[i]

                # assert corresponding voxel sizes exist for each downsampling
                voxel_sizes_dict: dict = volume_metadata.get("voxel_size")
                self.assertIsNotNone(voxel_sizes_dict)
                self.assertEqual(len(voxel_sizes_dict.keys()), len(volume_downsamplings))
                for downsampling in volume_downsamplings:
                    self.assertTrue(str(downsampling) in voxel_sizes_dict.keys())

                previous_voxel_size: list = voxel_sizes_dict.get('1')
                self.assertIsNotNone(previous_voxel_size)
                self.assertEqual(len(previous_voxel_size), 3)
                for i in range(1, len(volume_downsamplings)):
                    voxel_size_of_downsampling: list = voxel_sizes_dict.get(str(volume_downsamplings[i]))
                    self.assertIsNotNone(voxel_size_of_downsampling)
                    self.assertEqual(len(voxel_size_of_downsampling), 3)
                    for j in range(0, 3):
                        self.assertAlmostEqual(2 * previous_voxel_size[j], voxel_size_of_downsampling[j], delta=0.1)

                    previous_voxel_size = voxel_size_of_downsampling

                # assert origin exists
                origin: list = volume_metadata.get("origin")
                self.assertIsNotNone(origin)
                self.assertEqual(len(origin), 3)

                # downsampled grid dimensions are consistent
                grid_dimensions: list = volume_metadata.get("grid_dimensions")
                self.assertIsNotNone(grid_dimensions)
                self.assertEqual(len(grid_dimensions), 3)

                downsampled_grid_dict: dict = volume_metadata.get("sampled_grid_dimensions")
                self.assertIsNotNone(downsampled_grid_dict)
                self.assertEqual(len(downsampled_grid_dict.keys()), len(volume_downsamplings))
                for downsampling in volume_downsamplings:
                    self.assertTrue(str(downsampling) in downsampled_grid_dict.keys())

                previous_downsampled_grid: list = downsampled_grid_dict.get('1')
                self.assertIsNotNone(previous_downsampled_grid)
                self.assertEqual(len(previous_downsampled_grid), 3)
                for i in range(1, len(volume_downsamplings)):
                    downsampled_grid: list = downsampled_grid_dict.get(str(volume_downsamplings[i]))
                    self.assertIsNotNone(downsampled_grid)
                    self.assertEqual(len(downsampled_grid), 3)
                    for j in range(0, 3):
                        self.assertAlmostEqual(previous_downsampled_grid[j], 2 * downsampled_grid[j], delta=1)

                    previous_downsampled_grid = downsampled_grid

                # assert mean is consistent
                mean_dict: dict = volume_metadata.get("mean")
                self.assertIsNotNone(mean_dict)
                self.assertEqual(len(mean_dict.keys()), len(volume_downsamplings))
                for downsampling in volume_downsamplings:
                    self.assertTrue(str(downsampling) in mean_dict.keys())

                previous_mean = mean_dict.get('1')
                self.assertIsNotNone(previous_mean)
                previous_mean = float(previous_mean)
                for i in range(1, len(volume_downsamplings)):
                    mean = mean_dict.get(str(volume_downsamplings[i]))
                    self.assertIsNotNone(mean)
                    mean = float(mean)
                    self.assertAlmostEqual(mean, previous_mean, delta=abs(mean / 100))
                    previous_mean = mean

                # assert min is consistent
                min_dict: dict = volume_metadata.get("min")
                self.assertIsNotNone(min_dict)
                self.assertEqual(len(min_dict.keys()), len(volume_downsamplings))
                for downsampling in volume_downsamplings:
                    self.assertTrue(str(downsampling) in min_dict.keys())

                previous_min = min_dict.get('1')
                self.assertIsNotNone(previous_min)
                previous_min = float(previous_min)
                for i in range(1, len(volume_downsamplings)):
                    _min = min_dict.get(str(volume_downsamplings[i]))
                    self.assertIsNotNone(_min)
                    _min = float(_min)
                    self.assertAlmostEqual(_min, previous_min, delta=abs(_min / 100))
                    previous_min = _min

                # assert max is consistent
                max_dict: dict = volume_metadata.get("max")
                self.assertIsNotNone(max_dict)
                self.assertEqual(len(max_dict.keys()), len(volume_downsamplings))
                for downsampling in volume_downsamplings:
                    self.assertTrue(str(downsampling) in max_dict.keys())

                previous_max = max_dict.get('1')
                self.assertIsNotNone(previous_max)
                previous_max = float(previous_max)
                for i in range(1, len(volume_downsamplings)):
                    _max = max_dict.get(str(volume_downsamplings[i]))
                    self.assertIsNotNone(_max)
                    _max = float(_max)
                    self.assertAlmostEqual(_max, previous_max, delta=abs(_max * 0.6))  # TODO: check if this max is ok
                    previous_max = _max

                # assert std is consistent
                std_dict: dict = volume_metadata.get("std")
                self.assertIsNotNone(std_dict)
                self.assertEqual(len(std_dict.keys()), len(volume_downsamplings))
                for downsampling in volume_downsamplings:
                    self.assertTrue(str(downsampling) in std_dict.keys())

                previous_std = std_dict.get('1')
                self.assertIsNotNone(previous_std)
                previous_std = float(previous_std)
                for i in range(1, len(volume_downsamplings)):
                    _std = std_dict.get(str(volume_downsamplings[i]))
                    self.assertIsNotNone(_std)
                    _std = float(_std)
                    self.assertAlmostEqual(_std, previous_std, delta=abs(_std / 2))  # TODO: check if this std is ok
                    previous_std = _std

                print(body)
                annotaion_metadata = body.get("annotation")
                self.assertIsNotNone(annotaion_metadata)
        finally:
            pass


if __name__ == '__main__':
    unittest.main()
