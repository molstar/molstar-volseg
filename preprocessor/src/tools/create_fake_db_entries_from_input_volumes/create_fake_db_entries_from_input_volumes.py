from pathlib import Path
import shutil
from typing import List

import numpy as np
from db.implementations.local_disk.local_disk_preprocessed_db import LocalDiskPreprocessedDb
from preprocessor.main import preprocess_everything

# both volumes and segmentations
DIR_WITH_FILES_FOR_STORING = Path('preprocessor/data/fake_raw_input_files')

# input volume files
REAL_VOLUME_DIR = Path('preprocessor/data/real_volumes_for_conversion_to_fake_sff')


class RealVolumeToFakeSFFConverter:
    # Extend class
    from _create_fake_segmentation_from_real_volume import create_fake_segmentation_from_real_volume
    from _write_fake_segmentation_to_sff import write_fake_segmentation_to_sff
    from _helper_methods import get_list_of_input_volume_files, \
        clear_dir_with_files_for_storing, \
        convert_map_filename_to_entry_name

    def create_fake_sff_from_input_volumes(self, input_volumes_filepaths: List[Path], output_sff_dir: Path,
                                           source_db: str):
        '''Converts real volume file to fake sff'''
        for filepath in input_volumes_filepaths:
            entry_name = RealVolumeToFakeSFFConverter.convert_map_filename_to_entry_name(filepath.stem)
            # number of segments is random. Potentially can be less than this number
            # if it happen such that e.g. first 4 segments occupy all the space, and there is nothing left
            number_of_segments = np.random.randint(10, 15)
            segm_grid_and_ids = RealVolumeToFakeSFFConverter.create_fake_segmentation_from_real_volume(filepath, number_of_segments)
            grid = segm_grid_and_ids['grid']
            segm_ids = segm_grid_and_ids['ids']
            # print(f'segm ids provided to write_fake_segmentation_to_sff: {segm_ids}')
            # create dir for that entry
            (output_sff_dir / source_db / entry_name).mkdir(parents=True, exist_ok=True)

            RealVolumeToFakeSFFConverter.write_fake_segmentation_to_sff(
                output_sff_dir / source_db / entry_name / f'{entry_name}.hff',
                lattice_data=grid,
                segm_ids=segm_ids,
                json_for_debug=False
            )
            # copy input volume file to the same dir for that entry
            shutil.copy2(filepath, output_sff_dir / source_db / entry_name / filepath.name)


if __name__ == '__main__':
    SOURCE_DB = 'emdb'
    sff_converter = RealVolumeToFakeSFFConverter()
    RealVolumeToFakeSFFConverter.clear_dir_with_files_for_storing(DIR_WITH_FILES_FOR_STORING)
    list_of_input_volume_files = RealVolumeToFakeSFFConverter.get_list_of_input_volume_files(REAL_VOLUME_DIR)

    sff_converter.create_fake_sff_from_input_volumes(list_of_input_volume_files, DIR_WITH_FILES_FOR_STORING, SOURCE_DB)
    db = LocalDiskPreprocessedDb()
    db.remove_all_entries(namespace='emdb')
    preprocess_everything(db, DIR_WITH_FILES_FOR_STORING)
