import abc

import numpy as np

from db.interface.i_preprocessed_db import ProcessedVolumeSliceData
from db.interface.i_preprocessed_medatada import IPreprocessedMetadata


class IVolumeToCifConverter(abc.ABC):
    @abc.abstractmethod
    def convert(self, preprocessed_volume: ProcessedVolumeSliceData) -> np.ndarray:
        pass

    @abc.abstractmethod
    def convert_metadata(self, metadata: IPreprocessedMetadata):
        pass
