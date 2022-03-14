import abc

import numpy as np


class IVolumeToCifConverter(abc.ABC):
    @abc.abstractmethod
    def convert(self, preprocessed_volume: np.ndarray) -> object:  # TODO: add binary cif to the project
        pass

