from pathlib import Path
import re
import shutil
from typing import List

import numpy as np
from db.implementations.local_disk.local_disk_preprocessed_db import LocalDiskPreprocessedDb
from preprocessor._create_fake_segmentation_from_real_volume import create_fake_segmentation_from_real_volume
from preprocessor._write_fake_segmentation_to_sff import write_fake_segmentation_to_sff
from preprocessor.main import preprocess_everything

# both volumes and segmentations
DIR_WITH_FILES_FOR_STORING = Path('preprocessor/fake_raw_input_files/emdb')

# input volume files
REAL_VOLUME_DIR = Path('preprocessor/volume_files_for_fake_segmentations')

def convert_map_filename_to_entry_name(map_filename: str) -> str:
    components = re.split('_-', map_filename.lower())
    entry_name = f'{components[0]}-{components[1]}'
    return entry_name
    
def copy_input_volumes_to_dir_for_storing_in_db(input_volumes_filepaths: List[Path], dir_for_storing: Path):
    for filepath in input_volumes_filepaths:
        shutil.copy2(filepath, dir_for_storing / filepath.stem)

def create_fake_sff_from_input_volumes(input_volumes_filepaths: List[Path], output_sff_dir: Path):
    for filepath in input_volumes_filepaths:
        entry_name = convert_map_filename_to_entry_name(filepath.stem)
        # number of segments is random
        number_of_segments = np.random.randint(5,15) 
        segm_grid_and_ids = create_fake_segmentation_from_real_volume(filepath, number_of_segments)
        grid = segm_grid_and_ids['grid']
        segm_ids = segm_grid_and_ids['ids']
        write_fake_segmentation_to_sff(
            output_sff_dir / entry_name / f'{entry_name}.hff',
            lattice_data=grid,
            segm_ids=segm_ids,
            json_for_debug=True
            )    

def get_list_of_input_volume_files() -> List[Path]:
    # TODO: implement afterwards (e.g. collecting .MAP filepathes from DIR_WITH_FAKE_SFF)
    # TODO: write two Paths
    return [Path, Path]

if __name__ == '__main__':
    list_of_input_volume_files = get_list_of_input_volume_files()
    create_fake_sff_from_input_volumes(list_of_input_volume_files, DIR_WITH_FILES_FOR_STORING)
    copy_input_volumes_to_dir_for_storing_in_db(list_of_input_volume_files, DIR_WITH_FILES_FOR_STORING)
    db = LocalDiskPreprocessedDb()
    preprocess_everything(db, DIR_WITH_FILES_FOR_STORING)