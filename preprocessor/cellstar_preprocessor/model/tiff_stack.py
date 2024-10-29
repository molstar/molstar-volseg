
from dataclasses import dataclass
from pathlib import Path

from cellstar_db.models import TIFF_EXTENSIONS, DataKind
from cellstar_preprocessor.tools.tiff_stack_to_da_arr.tiff_stack_to_da_arr import tiff_stack_to_da_arr


@dataclass
class TIFFStackWrapper:
    dir_path: Path 
    kind: DataKind
    
    def __post_init__(self):
        # TODO: better way to find all tiff files
        tiff = list(self.dir_path.glob(TIFF_EXTENSIONS[0]))
        tif = list(self.dir_path.glob(TIFF_EXTENSIONS[1]))
        all = tif + tiff
        self.path = all[0]
    
    @property
    def to_array(self):
        return tiff_stack_to_da_arr(self.dir_path)
    