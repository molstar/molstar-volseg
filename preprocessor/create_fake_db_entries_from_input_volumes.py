from pathlib import Path
from typing import List

import numpy as np
from db.implementations.local_disk.local_disk_preprocessed_db import LocalDiskPreprocessedDb
from preprocessor._create_fake_segmentation_from_real_volume import create_fake_segmentation_from_real_volume
from preprocessor._write_fake_segmentation_to_sff import write_fake_segmentation_to_sff
from preprocessor.main import preprocess_everything

DIR_WITH_FAKE_SFF = Path('preprocessor/fake_segmentations')
   
def create_fake_sff_from_input_volumes(input_volumes_filepaths: List[Path], output_sff_dir: Path):
    for filepath in input_volumes_filepaths:
        segmentation_name = filepath.stem
        # number of segments is random
        number_of_segments = np.random.randint(5,15) 
        segm_grid_and_ids = create_fake_segmentation_from_real_volume(filepath, number_of_segments)
        grid = segm_grid_and_ids['grid']
        segm_ids = segm_grid_and_ids['ids']
        write_fake_segmentation_to_sff(
            output_sff_dir / segmentation_name,
            lattice_data=grid,
            segm_ids=segm_ids,
            json_for_debug=True
            )    

def get_list_of_input_volume_files() -> List[Path]:
    # TODO: implement afterwards (e.g. collecting files from some dir)
    # TODO: write two Paths
    return [Path, Path]

if __name__ == '__main__':
    list_of_input_volume_files = get_list_of_input_volume_files()
    create_fake_sff_from_input_volumes(list_of_input_volume_files, DIR_WITH_FAKE_SFF)
    db = LocalDiskPreprocessedDb()
    preprocess_everything(db, DIR_WITH_FAKE_SFF)