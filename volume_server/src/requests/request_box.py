from dataclasses import dataclass
from math import floor, ceil
from typing import Optional, Tuple

from db.interface.i_preprocessed_medatada import IPreprocessedMetadata
from volume_server.src.requests.volume_request.i_volume_request import IVolumeRequest

@dataclass
class RequestBox:
    downsampling_rate: int
    bottom_left: tuple[int, int, int] # inclusive
    top_right: tuple[int, int, int]  # inclusive

    @property
    def dimensions(self) -> tuple[int, int, int]:
        """Number of datapoints in each dimensions"""
        return tuple(self.top_right[i] - self.bottom_left[i] + 1 for i in range(3))

    @property
    def volume(self):
        nx, ny, nz = self.dimensions
        return nx * ny * nz


def calc_request_box(req_min: Tuple[float, float, float], req_max: Tuple[float, float, float], meta: IPreprocessedMetadata, downsampling_rate: int) -> Optional[RequestBox]:
    origin, voxel_size, grid_dimensions = meta.origin(), meta.voxel_size(downsampling_rate), meta.sampled_grid_dimensions(downsampling_rate)

    bottom_left = tuple(max(0, floor((req_min[i] - origin[i]) / voxel_size[i] )) for i in range(3))
    top_right = tuple(min(grid_dimensions[i] - 1, ceil((req_max[i] - origin[i]) / voxel_size[i] )) for i in range(3))

    # Check if the box is outside the available data
    if any(bottom_left[i] >= grid_dimensions[i] for i in range(3)) or any(top_right[i] < 0 for i in range(3)):
        return None

    return RequestBox(
        downsampling_rate=downsampling_rate,
        bottom_left=bottom_left,
        top_right=top_right
    )