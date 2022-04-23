from typing import List

import numpy as np

from db.interface.i_preprocessed_medatada import IPreprocessedMetadata


class FakePreprocessedMetadata(IPreprocessedMetadata):
    def json_metadata(self) -> str:
        return ""

    def mean(self, level: int) -> np.float64:
        return np.float64(0)

    def std(self, level: int) -> np.float64:
        return np.float64(0)

    def segmentation_lattice_ids(self) -> List[int]:
        return [0, 0, 0]

    def segmentation_downsamplings(self, lattice_id: int) -> List[int]:
        return [0, 0, 0]

    def volume_downsamplings(self) -> List[int]:
        return [0]

    def origin(self) -> List[float]:
        return [0, 0, 0]

    def voxel_size(self, downsampling_rate: int) -> List[float]:
        return [0, 0, 0]

    def grid_dimensions(self) -> List[int]:
        return [0, 0, 0]

    def lattice_ids(self) -> list[int]:
        return [0]

    def down_samplings(self, lattice_id: int) -> list[int]:
        return [0]
