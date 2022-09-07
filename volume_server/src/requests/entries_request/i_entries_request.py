import abc


class IEntriesRequest(abc.ABC):
    @abc.abstractmethod
    def keyword(self) -> str:
        pass

    @abc.abstractmethod
    def limit(self) -> int:
        pass

