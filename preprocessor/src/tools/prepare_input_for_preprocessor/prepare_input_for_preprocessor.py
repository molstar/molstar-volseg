
# e.g. emd-1832 or emd_1832
import argparse
from pathlib import Path
import re
import urllib.request
import os
import gzip
import shutil
import csv
import pandas as pd
import numpy as np

from preprocessor.src.preprocessors.implementations.sff.preprocessor.constants import CSV_WITH_ENTRY_IDS_FILE

# TODO: check if it works with abs path (starting with /)
# TODO: changed based on Lukas response
STATIC_INPUT_FILES_DIR = Path('/data/temp_static_entry_files_dir')

TEST_RAW_INPUT_FILES_DIR = Path('temp/test_raw_input_files_dir')

def csv_to_config_list_of_dicts(csv_file_path: Path) -> list[dict]:
    df = pd.read_csv(
        str(csv_file_path.resolve()),
        converters={
            'static_input_files': lambda x: bool(int(x))
            }
        )

    df = df.replace({np.nan: None})
    df['entry_id'] = df['entry_id'].str.lower()
    list_of_dicts = df.to_dict('records')

    return list_of_dicts

    

def prepare_input_for_preprocessor(config: list[dict], output_dir: Path) -> list[dict]:
    for entry in config:
        db = re.split('-|_', entry['entry_id'])[0].lower()
        id = re.split('-|_', entry['entry_id'])[-1]
        
        emdb_folder_name = db.upper() + '-' + id
        emdb_map_gz_file_name = db.lower() + '_' + id + '.map.gz'
        # https://www.ebi.ac.uk/em_static/emdb_sff/10/1014/emd_1014.hff.gz
        volume_browser_gz_file_name = db.lower() + '_' + id + '.hff.gz'
        preprocessor_folder_name = db.lower() + '-' + id

        # add to json object addtional info required on preprocessing step
        if db == 'emd':
            entry['source_db'] = 'emdb'
        elif db == 'empiar':
            entry['source_db'] = 'empiar'
        else:
            raise ValueError(f'Source db is not recognized: {db}')

        entry_folder = output_dir / entry['source_db'] / preprocessor_folder_name
        entry_folder.mkdir(parents=True, exist_ok=True)
        entry['single_entry'] = str(entry_folder.resolve())

        if entry['static_input_files']:
            static_segmentation_file_path = None
            static_folder_content = sorted((STATIC_INPUT_FILES_DIR / entry['source_db'] / preprocessor_folder_name).glob('*'))
            for item in static_folder_content:
                if item.is_file():
                    if item.suffix == '.hff':
                        static_segmentation_file_path = item
                    elif item.suffix == '.map' or item.suffix == '.ccp4' or item.suffix == '.mrc':
                        static_volume_file_path: Path = item

            static_map_output_path = entry_folder / static_volume_file_path.name
            shutil.copy2(static_volume_file_path, static_map_output_path)

            if static_segmentation_file_path:
                static_sff_output_path = entry_folder / static_segmentation_file_path.name
                shutil.copy2(static_segmentation_file_path, static_sff_output_path)
            
        else:
            if db == 'emd':
                # Get map
                map_gz_output_path = entry_folder / emdb_map_gz_file_name
                map_request_output = urllib.request.urlretrieve(
                    f'https://ftp.ebi.ac.uk/pub/databases/emdb/structures/{emdb_folder_name}/map/{emdb_map_gz_file_name}',
                    str(map_gz_output_path.resolve())
                )

                with gzip.open(str(map_gz_output_path.resolve()), 'rb') as f_in:
                    with open(str(map_gz_output_path.with_suffix('').resolve()), 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                map_gz_output_path.unlink()


                # get sff (.hff)
                sff_gz_output_path = entry_folder / volume_browser_gz_file_name

                # first two digits of emd ID?
                if len(id) == 4:
                    emdb_sff_prefix_number = id[0:2]
                    sff_request_output = urllib.request.urlretrieve(
                        f'https://www.ebi.ac.uk/em_static/emdb_sff/{emdb_sff_prefix_number}/{id}/{volume_browser_gz_file_name}',
                        str(sff_gz_output_path.resolve())
                    )
                elif len(id) == 5:
                    emdb_sff_prefix_number_1 = id[0:2]
                    emdb_sff_prefix_number_2 = id[2]
                    sff_request_output = urllib.request.urlretrieve(
                        f'https://www.ebi.ac.uk/em_static/emdb_sff/{emdb_sff_prefix_number_1}/{emdb_sff_prefix_number_2}/{id}/{volume_browser_gz_file_name}',
                        str(sff_gz_output_path.resolve())
                    )

                with gzip.open(str(sff_gz_output_path.resolve()), 'rb') as f_in:
                    with open(str(sff_gz_output_path.with_suffix('').resolve()), 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                sff_gz_output_path.unlink()
        
        
            # elif db == 'empiar':
            #     pass
        # for sff:
        # https://www.ebi.ac.uk/em_static/emdb_sff/empiar_10087_c2_tomo02/empiar_10087_c2_tomo02.hff.gz
        # https://www.ebi.ac.uk/em_static/emdb_sff/empiar_10087_e64_tomo03/empiar_10087_e64_tomo03.hff.gz
        # https://www.ebi.ac.uk/em_static/emdb_sff/empiar_10070_b3talongmusc20130301/empiar_10070_b3talongmusc20130301.hff.gz

        # for maps
        # any API?

        # 1. 2 empiar VB entries with same ID

        # updated config list of dicts
    return config
        

if __name__ == '__main__':
    config = csv_to_config_list_of_dicts(CSV_WITH_ENTRY_IDS_FILE)
    updated_config = prepare_input_for_preprocessor(config=config, output_dir=TEST_RAW_INPUT_FILES_DIR)