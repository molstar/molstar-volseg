from pydantic import BaseModel, root_validator, validator
from typing import Literal, Optional, Tuple

class VolumeRequestInfo(BaseModel):
    source: str
    structure_id: str
    segmentation_id: Optional[int] = None
    max_points: int  # = 0 ?
    data_kind: Literal["volume", "segmentation", "all"] = "all"  # TODO: use enum

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
