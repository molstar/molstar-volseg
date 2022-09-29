from dataclasses import dataclass


@dataclass
class GridSliceBox:
    downsampling_rate: int
    bottom_left: tuple[int, int, int]  # inclusive
    top_right: tuple[int, int, int]  # inclusive

    @property
    def dimensions(self) -> tuple[int, int, int]:
        """Number of datapoints in each dimensions"""
        return tuple(self.top_right[i] - self.bottom_left[i] + 1 for i in range(3))

    @property
    def volume(self):
        nx, ny, nz = self.dimensions
        return nx * ny * nz
