import abc
from pathlib import Path

class IDataPreprocessor(abc.ABC):
    @abc.abstractmethod
    def preprocess(self, file_path: Path):
        raise NotImplementedError