import logging
from typing import List

import numpy as np
from cellstar_db.models import (
    DownsamplingLevelInfo,
    MeshComponentNumbers,
    Metadata,
    VolumeMetadata,
)


class FileSystemVolumeMedatada(VolumeMetadata):
    def __init__(self, raw_metadata: Metadata):
        self.raw_metadata = raw_metadata

    def json_metadata(self) -> Metadata:
        return self.raw_metadata

    def db_name(self) -> str:
        return self.raw_metadata["entry_id"]["source_db_name"]

    def entry_id(self) -> str:
        return self.raw_metadata["entry_id"]["source_db_id"]

    def segmentation_lattice_ids(self) -> List[str]:
        if "segmentation_ids" in self.raw_metadata["segmentation_lattices"]:
            return self.raw_metadata["segmentation_lattices"]["segmentation_ids"]
        return []

    def segmentation_mesh_ids(self) -> list[int]:
        if "segmentation_ids" in self.raw_metadata["segmentation_meshes"]:
            return self.raw_metadata["segmentation_meshes"]["segmentation_ids"]
        return []

    def geometric_segmentation_ids(self) -> list[int]:
        if "segmentation_ids" in self.raw_metadata["geometric_segmentation"]:
            return self.raw_metadata["geometric_segmentation"]["segmentation_ids"]
        return []

    def segmentation_downsamplings(
        self, lattice_id: str
    ) -> List[DownsamplingLevelInfo]:
        s = []
        try:
            s = self.raw_metadata["segmentation_lattices"][
                "segmentation_sampling_info"
            ][lattice_id]["spatial_downsampling_levels"]
        except Exception as e:
            logging.error(e, stack_info=True, exc_info=True)
        return s

    def volume_downsamplings(self) -> List[DownsamplingLevelInfo]:
        return self.raw_metadata["volumes"]["volume_sampling_info"][
            "spatial_downsampling_levels"
        ]

    def origin(self, downsampling_rate: int) -> List[float]:
        return self.raw_metadata["volumes"]["volume_sampling_info"]["boxes"][
            str(downsampling_rate)
        ]["origin"]

    def voxel_size(self, downsampling_rate: int) -> List[float]:
        return self.raw_metadata["volumes"]["volume_sampling_info"]["boxes"][
            str(downsampling_rate)
        ]["voxel_size"]

    def grid_dimensions(self, downsampling_rate: int) -> List[int]:
        return self.raw_metadata["volumes"]["volume_sampling_info"]["boxes"][
            str(downsampling_rate)
        ]["grid_dimensions"]

    def sampled_grid_dimensions(self, level: int) -> List[int]:
        return self.raw_metadata["volumes"]["volume_sampling_info"]["boxes"][
            str(level)
        ]["grid_dimensions"]

    def mean(self, level: int, time: int, channel_id: str) -> np.float32:
        return np.float32(
            self.raw_metadata["volumes"]["volume_sampling_info"][
                "descriptive_statistics"
            ][str(level)][str(time)][str(channel_id)]["mean"]
        )

    def std(self, level: int, time: int, channel_id: str) -> np.float32:
        return np.float32(
            self.raw_metadata["volumes"]["volume_sampling_info"][
                "descriptive_statistics"
            ][str(level)][str(time)][str(channel_id)]["std"]
        )

    def max(self, level: int, time: int, channel_id: str) -> np.float32:
        return np.float32(
            self.raw_metadata["volumes"]["volume_sampling_info"][
                "descriptive_statistics"
            ][str(level)][str(time)][str(channel_id)]["max"]
        )

    def min(self, level: int, time: int, channel_id: str) -> np.float32:
        return np.float32(
            self.raw_metadata["volumes"]["volume_sampling_info"][
                "descriptive_statistics"
            ][str(level)][str(time)][str(channel_id)]["min"]
        )

    def mesh_component_numbers(self) -> MeshComponentNumbers:
        return self.raw_metadata["segmentation_meshes"]["mesh_component_numbers"]

    def detail_lvl_to_fraction(self) -> dict:
        return self.raw_metadata["segmentation_meshes"]["detail_lvl_to_fraction"]
