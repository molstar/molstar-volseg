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

    def model(self):
        return self.raw_metadata
    
    def dict(self):
        return self.raw_metadata.dict()

    def db_name(self) -> str:
        return self.raw_metadata.entry_id.source_db_name

    def entry_id(self) -> str:
        return self.raw_metadata.entry_id.source_db_id

    def segmentation_lattice_ids(self) -> List[str]:
        if self.raw_metadata.segmentation_lattices.ids is not None:
            return self.raw_metadata.segmentation_lattices.ids
        return []

    def segmentation_mesh_ids(self) -> list[int]:
        if self.raw_metadata.segmentation_meshes.ids is not None:
            return self.raw_metadata.segmentation_meshes.ids
        return []

    def geometric_segmentation_ids(self) -> list[int]:
        if self.raw_metadata.geometric_segmentation.ids is not None:
            return self.raw_metadata.geometric_segmentation.ids
        return []

    def segmentation_downsamplings(
        self, lattice_id: str
    ) -> List[DownsamplingLevelInfo]:
        if len(self.segmentation_lattice_ids()) > 0:
            s = []
            try:
                s = self.raw_metadata.segmentation_lattices.sampling_info[lattice_id].spatial_downsampling_levels
            except Exception as e:
                logging.error(e, stack_info=True, exc_info=True)
            return s
        else:
            return []

    def volume_downsamplings(self) -> List[DownsamplingLevelInfo]:
        return self.raw_metadata.volumes.sampling_info.spatial_downsampling_levels

    def origin(self, downsampling_rate: int) -> List[float]:
        return self.raw_metadata.volumes.sampling_info.boxes[
            str(downsampling_rate)
        ].origin

    def voxel_size(self, downsampling_rate: int) -> List[float]:
        return self.raw_metadata.volumes.sampling_info.boxes[
            str(downsampling_rate)
        ].voxel_size

    def grid_dimensions(self, downsampling_rate: int) -> List[int]:
        return self.raw_metadata.volumes.sampling_info.boxes[
            str(downsampling_rate)
        ].grid_dimensions

    def sampled_grid_dimensions(self, level: int) -> List[int]:
        return self.raw_metadata.volumes.sampling_info.boxes[
            str(level)
        ].grid_dimensions

    def descriptive_statistics(self, level: int, time: int, channel_id: str):
        return self.raw_metadata.volumes.sampling_info.descriptive_statistics[str(level)][str(time)][str(channel_id)]
        
    def mean(self, level: int, time: int, channel_id: str) -> np.float32:
        return np.float32(
            self.descriptive_statistics(level, time, channel_id).mean
        )

    def std(self, level: int, time: int, channel_id: str) -> np.float32:
        return np.float32(
            self.descriptive_statistics(level, time, channel_id).std
        )

    def max(self, level: int, time: int, channel_id: str) -> np.float32:
        return np.float32(
            self.descriptive_statistics(level, time, channel_id).max
        )

    def min(self, level: int, time: int, channel_id: str) -> np.float32:
        return np.float32(
            self.descriptive_statistics(level, time, channel_id).min
        )

    def mesh_component_numbers(self, segmentation_id: str, time: int):
        return self.raw_metadata.segmentation_meshes.metadata[segmentation_id].mesh_timeframes[time]

    def detail_lvl_to_fraction(self, segmentation_id: str, time: int):
        return self.raw_metadata.segmentation_meshes.metadata[segmentation_id].detail_lvl_to_fraction
