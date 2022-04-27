from pathlib import Path
import re
import shutil
from typing import List

import numpy as np
from db.implementations.local_disk.local_disk_preprocessed_db import LocalDiskPreprocessedDb
from preprocessor._create_fake_segmentation_from_real_volume import create_fake_segmentation_from_real_volume
from preprocessor._write_fake_segmentation_to_sff import write_fake_segmentation_to_sff
from preprocessor.main import preprocess_everything
from timeit import default_timer as timer

# both volumes and segmentations
DIR_WITH_FILES_FOR_STORING = Path('preprocessor/fake_raw_input_files')

# input volume files
REAL_VOLUME_DIR = Path('preprocessor/real_volumes_for_converstion_to_fake_sff')

def _clear_dir_with_files_for_storing(dirpath: Path):
    content = sorted(dirpath.glob('*'))
    for path in content:
        if path.is_file():
            path.unlink()
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)

def convert_map_filename_to_entry_name(map_filename: str) -> str:
    components = re.split('_|-', map_filename.lower())
    entry_name = f'{components[0]}-{components[1]}'
    return entry_name

def create_fake_sff_from_input_volumes(input_volumes_filepaths: List[Path], output_sff_dir: Path, source_db: str):
    for filepath in input_volumes_filepaths:
        entry_name = convert_map_filename_to_entry_name(filepath.stem)
        # number of segments is random. Potentially can be less than this number
        # if it happen such that e.g. first 4 segments occupy all the space, and there is nothing left
        number_of_segments = np.random.randint(10,15) 
        timer_fake_segm_from_vol_start = timer()
        segm_grid_and_ids = create_fake_segmentation_from_real_volume(filepath, number_of_segments)
        timer_fake_segm_from_vol_end = timer()
        print(f'fake segmentation is created for {filepath.stem}, took: {timer_fake_segm_from_vol_end - timer_fake_segm_from_vol_start}')
        grid = segm_grid_and_ids['grid']
        segm_ids = segm_grid_and_ids['ids']
        # print(f'segm ids provided to write_fake_segmentation_to_sff: {segm_ids}')
        # create dir for that entry
        (output_sff_dir / source_db / entry_name).mkdir(parents=True, exist_ok=True)
        
        timer_write_to_sff_start = timer()
        write_fake_segmentation_to_sff(
            output_sff_dir / source_db / entry_name / f'{entry_name}.hff',
            lattice_data=grid,
            segm_ids=segm_ids,
            json_for_debug=False
            )
            # copy input volume file to the same dir for that entry
        timer_write_to_sff_end = timer()
        print(f'SFF written, took {timer_write_to_sff_end - timer_write_to_sff_start}')
        shutil.copy2(filepath, output_sff_dir / source_db / entry_name / filepath.name)
        timer_copy_volume = timer()
        print(f'Copying volume file took {timer_copy_volume - timer_write_to_sff_end}')

def get_list_of_input_volume_files(input_volumes_dir: Path) -> List[Path]:
    list_of_input_volumes = []
    contents = sorted(input_volumes_dir.glob('*'))
    for path in contents:
        if path.is_file():
            ext = (path.suffix).lower()
            if ext == '.map' or ext == '.ccp4':
                list_of_input_volumes.append(path)

    return list_of_input_volumes

if __name__ == '__main__':
    SOURCE_DB = 'emdb'
    timer_init = timer()
    print('creation of fake db entries initiated')
    _clear_dir_with_files_for_storing(DIR_WITH_FILES_FOR_STORING)
    timer_clearing_dirs = timer()
    print(f'Directory clearing took: {round((timer_clearing_dirs - timer_init), 2)}')
    list_of_input_volume_files = get_list_of_input_volume_files(REAL_VOLUME_DIR)
    print(f'Fake SFF creation from input volumes started')
    timer_create_sff_from_input_start = timer()
    create_fake_sff_from_input_volumes(list_of_input_volume_files, DIR_WITH_FILES_FOR_STORING, SOURCE_DB)
    timer_create_sff_from_input_end = timer()
    print(f'Fake SFF creation from input volumes took: {timer_create_sff_from_input_end - timer_create_sff_from_input_start}')
    db = LocalDiskPreprocessedDb()
    db.remove_all_entries(namespace='emdb')
    preprocess_everything(db, DIR_WITH_FILES_FOR_STORING)
    timer_preprocessor_end = timer()
    print(f'Preprocessing step took: {timer_preprocessor_end - timer_create_sff_from_input_end}')