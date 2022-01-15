import abc


class IVolumeServer(abc.ABC):
    @abc.abstractmethod
    def root(self):
        pass

    def say_hello(self, user: str):
        pass
