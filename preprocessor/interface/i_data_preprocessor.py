import abc
from pathlib import Path

class IDataPreprocessor(abc.ABC):
    @abc.abstractmethod
    def preprocess(self, segm_file_path: Path, volume_file_path: Path):
        raise NotImplementedError