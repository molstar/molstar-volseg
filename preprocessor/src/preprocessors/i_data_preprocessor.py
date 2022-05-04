import abc
from pathlib import Path
import numpy as np

class IDataPreprocessor(abc.ABC):
    @abc.abstractmethod
    def preprocess(self, segm_file_path: Path, volume_file_path: Path, volume_force_dtype=np.float32):
        raise NotImplementedError