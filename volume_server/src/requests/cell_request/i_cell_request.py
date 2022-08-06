import abc


class ICellRequest(abc.ABC):
    @abc.abstractmethod
    def source(self) -> str:
        pass

    @abc.abstractmethod
    def structure_id(self) -> str:
        pass

    @abc.abstractmethod
    def segmentation_id(self) -> int:
        pass

    @abc.abstractmethod
    def max_points(self) -> int:
        pass

