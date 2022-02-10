import abc


class IPreprocessedVolume(abc.ABC):
    @abc.abstractmethod
    def volume(self) -> object:  # TODO: assign type to volume
        pass
