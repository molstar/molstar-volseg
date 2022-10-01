from pathlib import Path
from typing import Dict, Protocol, Tuple

from db.models import VolumeMetadata, VolumeSliceData


class DBReadContext(Protocol):
    async def read_slice(
        self,
        down_sampling_ratio: int,
        box: Tuple[Tuple[int, int, int], Tuple[int, int, int]],
        mode: str = "dask",
        timer_printout=False,
        lattice_id: int = 0,
    ) -> VolumeSliceData:
        """
        Reads a slice from a specific (down)sampling of segmentation and volume data
        from specific entry from DB based on key (e.g. EMD-1111), lattice_id (e.g. 0),
        downsampling ratio (1 => original data, 2 => downsampled by factor of 2 etc.),
        and slice box (vec3, vec3)
        """
        ...

    async def read_meshes(self, segment_id: int, detail_lvl: int) -> list[object]:
        """
        Returns list of meshes for a given segment, entry, detail lvl
        """
        ...

    async def read_volume_slice(
        self,
        down_sampling_ratio: int,
        box: Tuple[Tuple[int, int, int], Tuple[int, int, int]],
        mode: str = "dask",
        timer_printout=False,
    ) -> VolumeSliceData:
        ...

    async def read_segmentation_slice(
        self,
        lattice_id: int,
        down_sampling_ratio: int,
        box: Tuple[Tuple[int, int, int], Tuple[int, int, int]],
        mode: str = "dask",
        timer_printout=False,
    ) -> VolumeSliceData:
        ...

    def close(self) -> None:
        ...

    async def aclose(self) -> None:
        ...

    async def __aenter__(self) -> "DBReadContext":
        ...

    async def __aexit__(self, *args, **kwargs) -> None:
        ...


class VolumeServerDB(Protocol):
    async def contains(self, namespace: str, key: str) -> bool:
        ...

    def read(self, namespace: str, key: str) -> DBReadContext:
        ...

    async def read_metadata(self, namespace: str, key: str) -> VolumeMetadata:
        ...

    async def read_annotations(self, namespace: str, key: str) -> Dict:
        ...

    async def list_sources(self) -> list[str]:
        ...

    async def list_entries(self, source: str, limit: int) -> list[str]:
        ...

    async def store(self, namespace: str, key: str, temp_store_path: Path) -> bool:
        ...

    async def delete(self, namespace: str, key: str):
        ...
