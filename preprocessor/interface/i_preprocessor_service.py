import abc
from pathlib import Path
from typing import List

from preprocessor.interface.i_data_preprocessor import IDataPreprocessor


class IPreprocessorService(abc.ABC):
    @abc.abstractmethod
    def __init__(self, preprocessors: List[IDataPreprocessor]):
        raise NotImplementedError

    @abc.abstractmethod
    def get_raw_file_type(self, file_path: Path) -> str:
        raise NotImplementedError
    
    @abc.abstractmethod
    def get_preprocessor(self, file_type: str) -> IDataPreprocessor:
        raise NotImplementedError