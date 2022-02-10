import abc


class IVolumeRequest(abc.ABC):
    @abc.abstractmethod
    def structure_id(self) -> str:
        pass

    @abc.abstractmethod
    def x_min(self) -> float:
        pass

    @abc.abstractmethod
    def x_max(self) -> float:
        pass

    @abc.abstractmethod
    def y_min(self) -> float:
        pass

    @abc.abstractmethod
    def y_max(self) -> float:
        pass

    @abc.abstractmethod
    def z_min(self) -> float:
        pass

    @abc.abstractmethod
    def z_max(self) -> float:
        pass

