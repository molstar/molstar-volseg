import abc


class IMetadataRequest(abc.ABC):
    @abc.abstractmethod
    def source(self) -> str:
        pass

    @abc.abstractmethod
    def structure_id(self) -> str:
        pass
