import abc


class IMeshRequest(abc.ABC):
    @abc.abstractmethod
    def source(self) -> str:
        pass

    @abc.abstractmethod
    def id(self) -> str:
        pass

    @abc.abstractmethod
    def segment_id(self) -> int:
        pass

    @abc.abstractmethod
    def detail_lvl(self) -> int:
        pass

