import abc

import numpy


class IPreprocessedVolume(abc.ABC):
    @abc.abstractmethod
    def get_data(self) -> numpy.ndarray:  # TODO: assign type to volume
        pass
