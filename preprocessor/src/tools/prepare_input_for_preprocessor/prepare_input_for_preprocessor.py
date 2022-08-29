
# e.g. emd-1832 or emd_1832
from pathlib import Path
import re
import urllib.request
import os

# emd 1832 is not available!
LIST_OF_ENTRY_IDS = ['emd-1014', 'emd-1547']
RAW_INPUT_FILES_DIR = Path(__file__).parent.parent.parent.parent / 'data/raw_input_files'

def prepare_input_for_preprocessor(entry_ids: list):
    for entry_id in entry_ids:
        db = re.split('-|_', entry_id)[0]
        id = re.split('-|_', entry_id)[-1]

        emdb_folder_name = db.upper() + '-' + id
        emdb_map_gz_file_name = db.lower() + '_' + id + '.map.gz'
        # https://www.ebi.ac.uk/em_static/emdb_sff/10/1014/emd_1014.hff.gz
        volume_browser_gz_file_name = db.lower() + '_' + id + '.hff.gz'
        preprocessor_folder_name = db.lower() + '-' + id
        if db == 'emd':
            # TODO: try except?
            map_gz_output_path = RAW_INPUT_FILES_DIR / 'emdb' / preprocessor_folder_name / emdb_map_gz_file_name
            map_request_output = urllib.request.urlretrieve(
                f'https://ftp.ebi.ac.uk/pub/databases/emdb/structures/{emdb_folder_name}/map/{emdb_map_gz_file_name}',
                str(map_gz_output_path.resolve())
            )
            # gzipped_filepath = Path(request_output[0])
            
            # gunzip it, should delete gz and keep .map in correct location
            os.system('gunzip ' + str(map_gz_output_path.resolve()))
            # no .gz
            # map_filepath = map_gz_output_path.stem

            # get sff (.hff)
            sff_gz_output_path = RAW_INPUT_FILES_DIR / 'emdb' / preprocessor_folder_name / emdb_map_gz_file_name
            # first two digits of emd ID?
            emdb_sff_prefix_number = id[0:2]
            sff_request_output = urllib.request.urlretrieve(
                f'https://www.ebi.ac.uk/em_static/emdb_sff/{emdb_sff_prefix_number}/{id}/{volume_browser_gz_file_name}',
                str(sff_gz_output_path.resolve())
            )

            # gunzip it, should delete gz and keep .map in correct location
            os.system('gunzip ' + str(sff_gz_output_path.resolve()))    
        elif db == 'empiar':
            pass