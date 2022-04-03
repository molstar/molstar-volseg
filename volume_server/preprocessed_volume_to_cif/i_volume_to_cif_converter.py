import abc

import numpy as np

from db.interface.i_preprocessed_medatada import IPreprocessedMetadata


class IVolumeToCifConverter(abc.ABC):
    @abc.abstractmethod
    def convert(self, preprocessed_volume: np.ndarray) -> object:  # TODO: add binary cif to the project
        pass

    @abc.abstractmethod
    def convert_metadata(self, metadata: IPreprocessedMetadata):
        pass
