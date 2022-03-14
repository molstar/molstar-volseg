from typing import List

from db.interface.i_preprocessed_medatada import IPreprocessedMetadata


class FakePreprocessedMetadata(IPreprocessedMetadata):
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
