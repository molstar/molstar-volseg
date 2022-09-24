from dataclasses import dataclass
from pydantic import BaseModel, root_validator, validator
from typing import Literal, Optional, Tuple
from enum import Enum

class VolumeRequestDataKind(str, Enum):
    volume = "volume"
    segmentation = "segmentation"
    all = "all"

class VolumeRequestInfo(BaseModel):
    source: str
    structure_id: str
    segmentation_id: Optional[int] = None
    max_points: int
    data_kind: VolumeRequestDataKind = VolumeRequestDataKind.all

    @validator("segmentation_id")
    def _validate_segmentation_ui(cls, id: Optional[int], values):
        if id is None and values["data_kind"] != "volume":
            raise ValueError("segmentation_id must be defined for segmentation/all queries")

class VolumeRequestBox(BaseModel):
    bottom_left: Tuple[float, float, float]
    top_right: Tuple[float, float, float]

    @root_validator(skip_on_failure=True)
    def _validate_box(cls, values):
        bl, tr = values["bottom_left"], values["top_right"]
        if any(bl[i] >= tr[i] for i in range(3)):
            raise ValueError(f"{bl}, {tr} is not a valid request box")
        return values

@dataclass
class GridSliceBox:
    downsampling_rate: int
    bottom_left: tuple[int, int, int] # inclusive
    top_right: tuple[int, int, int] # inclusive

    @property
    def dimensions(self) -> tuple[int, int, int]:
        """Number of datapoints in each dimensions"""
        return tuple(self.top_right[i] - self.bottom_left[i] + 1 for i in range(3))

    @property
    def volume(self):
        nx, ny, nz = self.dimensions
        return nx * ny * nz
