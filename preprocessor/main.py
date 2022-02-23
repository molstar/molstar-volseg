
from pathlib import Path
from typing import Dict, List
from db.implementations.local_disk.local_disk_preprocessed_db import LocalDiskPreprocessedDb

from db.interface.i_preprocessed_db import IPreprocessedDb
from preprocessor.implementations.preprocessor_service import PreprocessorService

RAW_INPUT_FILES_DIR = Path(__file__).parent / 'raw_input_files'

def obtain_paths_to_all_files(raw_input_files_dir: Path) -> Dict[List[Dict]]:
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
    # TODO: later this dict can be compiled during batch raw file download, it should be easier than doing it like this
    # d = {}
    # for dir_path in raw_input_files_dir.iterdir():
    #     if dir_path.is_dir():
    #         d[dir_path.stem] = []
    #         for subdir_path in dir_path.iterdir():
    #             if subdir_path.is_dir():
    #                 content = sorted(subdir_path).glob('*')
    #                 for item in content:
    #                     if item.is_file():
    #                         if item.suffix == '.hff':

    #                         if item.suffix == '.map':
    #                 d[dir_path.stem].append(
    #                     {
    #                         'id': subdir_path.stem,
    #                         # 'volume_file_path': ,
    #                         # 'segmentation_file_path': ,
    #                     }
    #                 )

    # temp implementation
    dummy_dict = {
        'emdb': [
            {
                'id': 'emd-1832',
                'volume_file_path': Path(__file__) / RAW_INPUT_FILES_DIR / 'emdb' / 'emd-1832' / 'EMD-1832.map',
                'segmentation_file_path': Path(__file__) / RAW_INPUT_FILES_DIR / 'emdb' / 'emd-1832' / 'emd_1832.hff',
            }
        ]
    }
    return dummy_dict

def preprocess_everything(db: IPreprocessedDb, raw_input_files_dir: Path) -> None:
    preprocessor_service = PreprocessorService()
    files_dict = obtain_paths_to_all_files(raw_input_files_dir)
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
    db = LocalDiskPreprocessedDb()
    preprocess_everything(db, RAW_INPUT_FILES_DIR)