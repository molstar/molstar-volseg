import abc
from pathlib import Path
from typing import TYPE_CHECKING, Dict, Tuple, TypedDict

import numpy as np
if TYPE_CHECKING:
    from db.implementations.local_disk.local_disk_preprocessed_db import ReadContext

from db.interface.i_preprocessed_medatada import IPreprocessedMetadata

class SegmentationSliceData(TypedDict):
    # array with set ids
    category_set_ids: np.ndarray
    # dict mapping set ids to the actual segment ids (e.g. for set id=1, there may be several segment ids)
    category_set_dict: Dict

class ProcessedVolumeSliceData(TypedDict):
    # changed segm slice to another typeddict
    segmentation_slice: SegmentationSliceData
    volume_slice: np.ndarray

class IReadOnlyPreprocessedDb(abc.ABC):
    @abc.abstractmethod
    async def contains(self, namespace: str, key: str) -> bool:
        pass

    @abc.abstractmethod
    def read(self, namespace: str, key: str) -> "ReadContext":
        pass

    @abc.abstractmethod
    async def read_metadata(self, namespace: str, key: str) -> IPreprocessedMetadata:
        pass

    @abc.abstractmethod
    async def read_annotations(self, namespace: str, key: str) -> Dict:
        pass

class IPreprocessedDb(IReadOnlyPreprocessedDb, abc.ABC):
    @abc.abstractmethod
    async def store(self, namespace: str, key: str, temp_store_path: Path) -> bool:
        pass
