from pydantic.dataclasses import dataclass


@dataclass
class GridSliceBox(object):
    downsampling_rate: int
    """Datapoint spacing relative to the original"""
    bottom_left: tuple[int, int, int]
    """x,y,z indices of the bottom-left datapoint (INCLUSIVE)"""
    top_right: tuple[int, int, int]
    """x,y,z indices of the top-right datapoint (INCLUSIVE)"""

    @property
    def dimensions(self) -> tuple[int, int, int]:
        """Number of datapoints in each dimensions"""
        return tuple(self.top_right[i] - self.bottom_left[i] + 1 for i in range(3))  # type: ignore  # length is 3

    @property
    def volume(self) -> int:
        """Total volume of the box (number of datapoints)"""
        nx, ny, nz = self.dimensions
        return nx * ny * nz
