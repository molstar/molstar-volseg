from pathlib import Path
from typing import List

from preprocessor.interface.i_data_preprocessor import IDataPreprocessor
from preprocessor.interface.i_preprocessor_service import IPreprocessorService

class SFFPreprocessorService(IPreprocessorService):
    def __init__(self, preprocessors: List[IDataPreprocessor]):
        pass

    def get_raw_file_type(self, file_path: Path):
        pass

    def get_preprocessor(self, file_type: str):
        pass