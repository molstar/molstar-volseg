import abc

from db.interface.i_preprocessed_medatada import IPreprocessedMetadata
from db.interface.i_preprocessed_volume import IPreprocessedVolume


class IReadOnlyPreprocessedDb(abc.ABC):
    @abc.abstractmethod
    async def contains(self, namespace: str, key: str) -> bool:
        pass

    @abc.abstractmethod
    async def read(self, namespace: str, key: str, down_sampling_ratio: int) -> IPreprocessedVolume:
        pass

    @abc.abstractmethod
    async def read_metadata(self, namespace: str, key: str) -> IPreprocessedMetadata:
        pass


class IPreprocessedDb(IReadOnlyPreprocessedDb, abc.ABC):
    @abc.abstractmethod
    async def store(self, namespace: str, key: str, value: object) -> bool:
        pass
