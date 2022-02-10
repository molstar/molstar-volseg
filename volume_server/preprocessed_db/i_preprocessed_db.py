import abc

from volume_server.preprocessed_db.i_preprocessed_volume import IPreprocessedVolume


class IReadOnlyPreprocessedDb(abc.ABC):
    @abc.abstractmethod
    async def contains(self, namespace: str, key: str) -> bool:
        pass

    @abc.abstractmethod
    async def read(self, namespace: str, key: str) -> IPreprocessedVolume:
        pass


class IPreprocessedDb(IReadOnlyPreprocessedDb, abc.ABC):
    @abc.abstractmethod
    async def store(self, namespace: str, key: str, value: str) -> bool:
        pass
