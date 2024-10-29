

from pathlib import Path

from cellstar_db.models import AssetKind
from pydantic import BaseModel


class InputT(BaseModel):
    path: Path | list[Path]
    kind: AssetKind


class OMETIFFImageInput(InputT):
    pass


class ExtraDataInput(InputT):
    pass


class STLSegmentationInput(InputT):
    pass


class TIFFSegmentationStackDirInput(InputT):
    pass


class OMETIFFSegmentationInput(InputT):
    pass


class SFFInput(InputT):
    pass


class OMEZARRInput(InputT):
    pass


class MAPInput(InputT):
    pass


class CustomAnnotationsInput(InputT):
    pass


class NIIVolumeInput(InputT):
    pass


class NIISegmentationInput(InputT):
    pass


class MaskInput(InputT):
    pass


class TIFFImageStackDirInput(InputT):
    pass


class GeometricSegmentationInput(InputT):
    pass