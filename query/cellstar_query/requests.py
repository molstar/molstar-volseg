from enum import Enum
from typing import Optional, Tuple

from pydantic import BaseModel, root_validator, validator


class VolumeRequestDataKind(str, Enum):
    volume = "volume"
    segmentation = "segmentation"
    all = "all"


class VolumeRequestInfo(BaseModel):
    source: str
    structure_id: str
    segmentation_id: Optional[str] = None
    channel_id: Optional[str] = None
    time: int
    max_points: int
    data_kind: VolumeRequestDataKind = VolumeRequestDataKind.all

    @validator("segmentation_id")
    def _validate_segmentation_ui(cls, id: Optional[str], values):
        if id is None and values["data_kind"] != "volume":
            raise ValueError(
                "segmentation_id must be defined for segmentation/all queries"
            )
        return id

    @validator("channel_id")
    def _validate_channel_id(cls, id: Optional[str], values):
        if id is None and values["data_kind"] != "segmentation":
            raise ValueError("channel_id must be defined for volume queries")
        return id


class VolumeRequestBox(BaseModel):
    bottom_left: Tuple[float, float, float]
    top_right: Tuple[float, float, float]

    @root_validator(skip_on_failure=True)
    def _validate_box(cls, values):
        bl, tr = values["bottom_left"], values["top_right"]
        if any(bl[i] >= tr[i] for i in range(3)):
            raise ValueError(f"{bl}, {tr} is not a valid request box")
        return values


class EntriesRequest(BaseModel):
    limit: int
    keyword: str


class GeometricSegmentationRequest(BaseModel):
    source: str
    structure_id: str
    segmentation_id: str
    time: int


class MeshRequest(BaseModel):
    source: str
    structure_id: str
    segmentation_id: str
    segment_id: int
    detail_lvl: int
    time: int


class MetadataRequest(BaseModel):
    source: str
    structure_id: str
