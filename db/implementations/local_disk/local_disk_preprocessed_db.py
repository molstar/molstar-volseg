import numpy

from .local_disk_preprocessed_medata import LocalDiskPreprocessedMetadata
from .local_disk_preprocessed_volume import LocalDiskPreprocessedVolume
from db.interface.i_preprocessed_db import IPreprocessedDb
from db.interface.i_preprocessed_volume import IPreprocessedVolume
from ...interface.i_preprocessed_medatada import IPreprocessedMetadata


class LocalDiskPreprocessedDb(IPreprocessedDb):
    @staticmethod
    def __path_to_object__(namespace: str, key: str) -> str:
        return "db/" + namespace + "/" + key

    async def contains(self, namespace: str, key: str) -> bool:
        return True  # path.isfile(self.__path_to_object__(namespace, key))

    async def store(self, namespace: str, key: str, value: object) -> bool:
        return True

    async def read(self, namespace: str, key: str, down_sampling_ratio: int) -> IPreprocessedVolume:
        read_zarr = numpy.ndarray([0])  # read the same way you read until now
        return LocalDiskPreprocessedVolume(read_zarr)

    async def read_metadata(self, namespace: str, key: str) -> IPreprocessedMetadata:
        read_json_of_metadata = ""  # read the same way you read until now
        return LocalDiskPreprocessedMetadata(read_json_of_metadata)
