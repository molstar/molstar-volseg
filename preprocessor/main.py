

from pathlib import Path
from typing import Dict, List

from db.interface.i_preprocessed_db import IPreprocessedDb
from preprocessor.implementations.preprocessor_service import PreprocessorService


def obtain_paths_to_all_files() -> List[Dict]:
    # dict of lists: keys = source names (e.g. EMDB), values = Lists of Path objects
    pass

def preprocess_everything(db: IPreprocessedDb) -> None:
    preprocessor_service = PreprocessorService()
    all_files_to_preprocess_by_source = obtain_paths_to_all_files()
    for source_name, paths_to_all_files in all_files_to_preprocess_by_source:
        for file_path in paths_to_all_files:
            file_type = preprocessor_service.get_raw_file_type(file_path)
            file_preprocessor = preprocessor_service.get_preprocessor(file_type)
            processed_data_temp_path = file_preprocessor.preprocess(file_path)
            db.store(namespace=source_name, key=file_path.stem, temp_store_path=processed_data_temp_path)

if __name__ == '__main__':
    preprocess_everything()