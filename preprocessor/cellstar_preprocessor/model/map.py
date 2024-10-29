from pathlib import Path
from dataclasses import dataclass

from cellstar_db.models import DataKind, MapHeader, MapParameters
from cellstar_preprocessor.tools.parse_map.parse_map import parse_map

@dataclass
class MapWrapper:
    path: Path
    kind: DataKind
    params: MapParameters | None = None
    
    @property
    def parsed(self):
        dtype = self.params.dtype if self.params.dtype else None
        voxel_size = self.params.voxel_size if self.params.voxel_size else None
        return parse_map(
            self.path, voxel_size, dtype, self.kind
        )
    
    @property
    def header(self):
        return MapHeader(self.parsed.header)