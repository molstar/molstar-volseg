import logging
from typing import Dict, List

import numpy as np

from db.models import MeshComponentNumbers, VolumeMetadata


class FileSystemVolumeMedatada(VolumeMetadata):
    def __init__(self, raw_metadata: Dict):
        self.raw_metadata = raw_metadata

    def json_metadata(self) -> str:
        return self.raw_metadata

    def segmentation_lattice_ids(self) -> List[int]:
        return self.raw_metadata["segmentation_lattices"]["segmentation_lattice_ids"]

    def segmentation_downsamplings(self, lattice_id: int) -> List[int]:
        s = []
        try:
            s = self.raw_metadata["segmentation_lattices"][
                "segmentation_downsamplings"
            ][str(lattice_id)]
        except Exception as e:
            logging.error(e, stack_info=True, exc_info=True)
        return s

    def volume_downsamplings(self) -> List[int]:
        return self.raw_metadata["volumes"]["volume_downsamplings"]

    def origin(self) -> List[float]:
        return self.raw_metadata["volumes"]["origin"]

    def voxel_size(self, downsampling_rate: int) -> List[float]:
        return self.raw_metadata["volumes"]["voxel_size"][str(downsampling_rate)]

    def grid_dimensions(self) -> List[int]:
        return self.raw_metadata["volumes"]["grid_dimensions"]

    def sampled_grid_dimensions(self, level: int) -> List[int]:
        return self.raw_metadata["volumes"]["sampled_grid_dimensions"][str(level)]

    def mean(self, level: int) -> np.float32:
        return np.float32(self.raw_metadata["volumes"]["mean"][str(level)])

    def std(self, level: int) -> np.float32:
        return np.float32(self.raw_metadata["volumes"]["std"][str(level)])

    def max(self, level: int) -> np.float32:
        return np.float32(self.raw_metadata["volumes"]["max"][str(level)])

    def min(self, level: int) -> np.float32:
        return np.float32(self.raw_metadata["volumes"]["min"][str(level)])

    def mesh_component_numbers(self) -> MeshComponentNumbers:
        return self.raw_metadata["segmentation_meshes"]["mesh_component_numbers"]

    def detail_lvl_to_fraction(self) -> dict:
        return self.raw_metadata["segmentation_meshes"]["detail_lvl_to_fraction"]
