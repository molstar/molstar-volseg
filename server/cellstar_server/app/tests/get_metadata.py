import unittest
from typing import TypedDict

import requests
from cellstar_db.models import (
    DownsamplingLevelInfo,
    SamplingBox,
    VolumeDescriptiveStatistics,
)
from cellstar_server.app.tests._test_server_runner import ServerTestBase


class VolumeDescriptiveStatisticsIndicators(TypedDict):
    mean: list[float]
    min: list[float]
    max: list[float]
    std: list[float]


class FetchMetadataTest(ServerTestBase):
    def test(self):
        try:
            with self.server.run_in_thread():
                # idr/idr-6001247
                r = requests.get(f"{self.serverUrl()}/v1/emdb/emd-1832/metadata/")
                # r = requests.get(f"{self.serverUrl()}/v1/idr/idr-6001247/metadata/")
                self.assertEqual(r.status_code, 200)
                body: dict = dict(r.json())
                self.assertIsNotNone(body)

                # check grid metadata
                grid_metadata = body.get("grid")
                self.assertIsNotNone(grid_metadata)
                grid_metadata: dict = dict(grid_metadata)

                # get volumes metadata
                volume_metadata = grid_metadata.get("volumes")

                volume_sampling_info: dict = volume_metadata.get("volume_sampling_info")
                volume_downsamplings: list[DownsamplingLevelInfo] = (
                    volume_sampling_info.get("spatial_downsampling_levels")
                )

                self.assertIsNotNone(volume_downsamplings)
                self.assertTrue(len(volume_downsamplings) > 0)

                # get segmentation metadata
                segmentation_metadata = grid_metadata.get("segmentation_lattices")

                # assert all segmentations contain valid downsamplings
                segmentation_lattices: list = segmentation_metadata.get(
                    "segmentation_ids"
                )
                self.assertIsNotNone(segmentation_lattices)
                self.assertTrue(len(segmentation_lattices) > 0)
                segmentation_sampling_info: dict = segmentation_metadata.get(
                    "segmentation_sampling_info"
                )
                self.assertIsNotNone(segmentation_sampling_info)

                for segmentation_lattice in segmentation_lattices:
                    segmentation_downsamplings: list = segmentation_sampling_info.get(
                        segmentation_lattice
                    ).get("spatial_downsampling_levels")
                    self.assertIsNotNone(segmentation_downsamplings)

                boxes_dict: dict[int, SamplingBox] = volume_sampling_info.get("boxes")
                # first check if number of keys of boxes == to length of volume downsamplings
                self.assertIsNotNone(boxes_dict)
                self.assertEqual(len(boxes_dict.keys()), len(volume_downsamplings))

                # then check that each downsampling is in volume downsamplings
                for downsampling_lvl_info in volume_downsamplings:
                    # downsamplings are dicts
                    if downsampling_lvl_info.available == True:
                        self.assertTrue(
                            str(downsampling_lvl_info.level) in boxes_dict.keys()
                        )

                # assert origin exists for each box
                for idx, box in boxes_dict.items():
                    origin: list = box.get("origin")
                    self.assertIsNotNone(origin)
                    self.assertEqual(len(origin), 3)

                    # downsampled grid dimensions are consistent
                    grid_dimensions: list = box.get("grid_dimensions")
                    self.assertIsNotNone(grid_dimensions)
                    self.assertEqual(len(grid_dimensions), 3)

                    # then check that voxel size has length of 3 (3 dimensions)
                    voxel_size: list = box.get("voxel_size")
                    self.assertIsNotNone(voxel_size)
                    self.assertEqual(len(voxel_size), 3)

                ds_grouped = {}

                # create dict
                # where key = f"{time}-{channel_id}"
                # value = object with attrs mean, min, max, std
                # if key not exist = create that object
                # if exists - append to existing object

                descriptive_statistics: dict[
                    int, dict[int, dict[str, VolumeDescriptiveStatistics]]
                ] = volume_sampling_info.get("descriptive_statistics")

                for downsampling_lvl_info in volume_downsamplings:
                    # downsamplings are dicts
                    if downsampling_lvl_info.available == True:
                        self.assertTrue(
                            str(downsampling_lvl_info.level)
                            in descriptive_statistics.keys()
                        )

                for resolution, resolution_ds in descriptive_statistics.items():
                    for time, time_ds in resolution_ds.items():
                        for channel_id, channel_ds in time_ds.items():
                            unique_key = f"{time}-{channel_id}"
                            if unique_key not in ds_grouped:
                                data: VolumeDescriptiveStatisticsIndicators = {
                                    "max": [channel_ds.get("max")],
                                    "mean": [channel_ds.get("mean")],
                                    "min": [channel_ds.get("min")],
                                    "std": [channel_ds.get("std")],
                                }
                                ds_grouped[unique_key] = data
                            # data for that time and channel exists, append to it
                            else:
                                existing_data: VolumeDescriptiveStatisticsIndicators = (
                                    ds_grouped[unique_key]
                                )
                                for indicator in existing_data:
                                    existing_data[indicator].append(
                                        channel_ds.get(indicator)
                                    )

                # then for each indicator do comparison
                for unique_key in ds_grouped:
                    ds: VolumeDescriptiveStatisticsIndicators = ds_grouped[unique_key]
                    self.assertIsNotNone(ds)

                    for indicator in ds:
                        self.assertEqual(len(ds[indicator]), len(volume_downsamplings))

                    previous_mean = ds["mean"][0]
                    for i in range(1, len(ds["mean"])):
                        new_mean = ds["mean"][i]
                        self.assertAlmostEqual(
                            previous_mean, new_mean, delta=abs(new_mean / 50)
                        )
                        previous_mean = new_mean

                    previous_min = ds["min"][0]
                    for i in range(1, len(ds["min"])):
                        new_min = ds["min"][i]
                        self.assertAlmostEqual(
                            previous_min, new_min, delta=abs(new_min / 50)
                        )
                        previous_min = new_min

                    previous_max = ds["max"][0]
                    for i in range(1, len(ds["max"])):
                        new_max = ds["max"][i]
                        self.assertAlmostEqual(
                            previous_max, new_max, delta=abs(new_max * 0.6)
                        )
                        previous_max = new_max

                    previous_std = ds["std"][0]
                    for i in range(1, len(ds["std"])):
                        new_std = ds["std"][i]
                        self.assertAlmostEqual(
                            previous_std, new_std, delta=abs(new_std / 2)
                        )
                        previous_std = new_std

                print(body)
                annotaion_metadata = body.get("annotation")
                self.assertIsNotNone(annotaion_metadata)
        finally:
            pass


if __name__ == "__main__":
    unittest.main()
