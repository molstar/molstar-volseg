import abc
from pathlib import Path
from typing import Dict, Tuple, TypedDict

import numpy as np

from db.interface.i_preprocessed_medatada import IPreprocessedMetadata


class ProcessedVolumeSliceData(TypedDict):
    segmentation_slice: np.ndarray
    volume_slice: np.ndarray


class IReadOnlyPreprocessedDb(abc.ABC):
    @abc.abstractmethod
    async def contains(self, namespace: str, key: str) -> bool:
        pass

    @abc.abstractmethod
    async def read(self, namespace: str, key: str, lattice_id: int, down_sampling_ratio: int) -> Dict:
        pass
    
    @abc.abstractmethod
    async def read_slice(self, namespace: str, key: str, lattice_id: int, down_sampling_ratio: int, box: Tuple[Tuple[int, int, int], Tuple[int, int, int]], mode: str = 'dask') -> ProcessedVolumeSliceData:
        pass

    @abc.abstractmethod
    async def read_metadata(self, namespace: str, key: str) -> IPreprocessedMetadata:
        pass


class IPreprocessedDb(IReadOnlyPreprocessedDb, abc.ABC):
    @abc.abstractmethod
    async def store(self, namespace: str, key: str, temp_store_path: Path) -> bool:
        pass
