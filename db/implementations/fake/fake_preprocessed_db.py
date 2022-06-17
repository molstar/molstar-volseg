from os import path
from typing import Tuple, Dict

import numpy

from .fake_preprocessed_metadata import FakePreprocessedMetadata
from .fake_preprocessed_volume import FakePreprocessedVolume
from db.interface.i_preprocessed_db import IPreprocessedDb
from db.interface.i_preprocessed_volume import IPreprocessedVolume
from ...interface.i_preprocessed_medatada import IPreprocessedMetadata


class FakePreprocessedDb(IPreprocessedDb):
    async def read_slice(self, namespace: str, key: str, lattice_id: int, down_sampling_ratio: int,
                         box: Tuple[Tuple[int, int, int], Tuple[int, int, int]], mode: str = 'dask') -> Dict:
        return dict()

    async def read_metadata(self, namespace: str, key: str) -> IPreprocessedMetadata:
        return FakePreprocessedMetadata()

    @staticmethod
    def _path_to_object(namespace: str, key: str) -> str:
        return path.join("../../..", namespace, key)

    async def contains(self, namespace: str, key: str) -> bool:
        return True  # path.isfile(self._path_to_object(namespace, key))

    async def store(self, namespace: str, key: str, value: object) -> bool:
        return True

    async def read(self, namespace: str, key: str, lattice_id: int,  down_sampling_ratio: int) -> IPreprocessedVolume:
        return FakePreprocessedVolume(numpy.array([0]))
