

from pathlib import Path
from typing import Dict, List

from db.interface.i_preprocessed_db import IPreprocessedDb
from preprocessor.implementations.preprocessor_service import PreprocessorService


def obtain_paths_to_all_files() -> Dict[List[Dict]]:
    '''
    Returns dict of lists:
    keys = source names (e.g. EMDB), values = Lists of Dicts.
    In each (sub)Dict, Path objects to volume and segmentation files are provided along with entry name.
    Both files are located in one dir (name = entry name)
    ----
    Example:
    {'emdb': [
        {
            'id': emd-1832,
            'volume_file_path': Path(...),
            'segmentation_file_path': Path(...),
        },
        {
            ...
        },
    ]}
    '''
    # TODO: all ids lowercase!
    pass

def preprocess_everything(db: IPreprocessedDb) -> None:
    preprocessor_service = PreprocessorService()
    files_dict = obtain_paths_to_all_files()
    for source_name, source_entries in files_dict.items():
        for entry in source_entries:
            segm_file_type = preprocessor_service.get_raw_file_type(entry['segmentation_file_path'])
            file_preprocessor = preprocessor_service.get_preprocessor(segm_file_type)
            processed_data_temp_path = file_preprocessor.preprocess(
                segm_file_path = entry['segmentation_file_path'],
                volume_file_path = entry['volume_file_path']
            )
            db.store(namespace=source_name, key=entry.id, temp_store_path=processed_data_temp_path)

if __name__ == '__main__':
    preprocess_everything()