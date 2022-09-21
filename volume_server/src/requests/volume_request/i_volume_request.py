import abc


class IVolumeRequest(abc.ABC):
    @abc.abstractmethod
    def source(self) -> str:
        pass

    @abc.abstractmethod
    def structure_id(self) -> str:
        pass

    @abc.abstractmethod
    def segmentation_id(self) -> int:
        pass

    # TODO: replace x/y/z_min/max with bottom_left/top_right tuples
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

    @abc.abstractmethod
    def max_points(self) -> int:
        pass

