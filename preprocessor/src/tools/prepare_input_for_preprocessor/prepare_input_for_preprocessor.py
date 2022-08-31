
# e.g. emd-1832 or emd_1832
import argparse
from pathlib import Path
import re
import urllib.request
import os
import gzip
import shutil

# without empiar for now
# they require special handling (maps, links to sff)
# 11
LIST_OF_ENTRY_IDS = [
    'emd-1014', 'emd-1547', 'EMD-5250', 'EMD-6338',	
    'EMD-5143',
    'EMD-2847',
    'EMD-1181',
    'EMD-1963',
    'EMD-1080',
    'EMD-20293',
    'EMD-1832'
    ]
RAW_INPUT_FILES_DIR = Path(__file__).parent.parent.parent.parent / 'data/raw_input_files'

def parse_script_args():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output_dir", type=Path, default=RAW_INPUT_FILES_DIR, help='path to dir where files will be downloaded')
    args=parser.parse_args()
    return args

def prepare_input_for_preprocessor(entry_ids: list, output_dir: Path):
    for entry_id in entry_ids:
        db = re.split('-|_', entry_id)[0].lower()
        id = re.split('-|_', entry_id)[-1]

        emdb_folder_name = db.upper() + '-' + id
        emdb_map_gz_file_name = db.lower() + '_' + id + '.map.gz'
        # https://www.ebi.ac.uk/em_static/emdb_sff/10/1014/emd_1014.hff.gz
        volume_browser_gz_file_name = db.lower() + '_' + id + '.hff.gz'
        preprocessor_folder_name = db.lower() + '-' + id
        if db == 'emd':
            # TODO: try except?
            map_gz_output_path = output_dir / 'emdb' / preprocessor_folder_name / emdb_map_gz_file_name
            map_gz_output_path.parent.mkdir(parents=True, exist_ok=True)
            map_request_output = urllib.request.urlretrieve(
                f'https://ftp.ebi.ac.uk/pub/databases/emdb/structures/{emdb_folder_name}/map/{emdb_map_gz_file_name}',
                str(map_gz_output_path.resolve())
            )
            
            # won't work on windows
            # gunzip it, should delete gz and keep .map in correct location
            # os.system('gunzip ' + str(map_gz_output_path.resolve()))
            
            with gzip.open(str(map_gz_output_path.resolve()), 'rb') as f_in:
                with open(str(map_gz_output_path.with_suffix('').resolve()), 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            map_gz_output_path.unlink()

            # get sff (.hff)
            sff_gz_output_path = output_dir / 'emdb' / preprocessor_folder_name / volume_browser_gz_file_name
            sff_gz_output_path.parent.mkdir(parents=True, exist_ok=True)

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

            # gunzip it, should delete gz and keep .map in correct location
            # os.system('gunzip ' + str(sff_gz_output_path.resolve()))

            with gzip.open(str(sff_gz_output_path.resolve()), 'rb') as f_in:
                with open(str(sff_gz_output_path.with_suffix('').resolve()), 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            sff_gz_output_path.unlink()
                
        elif db == 'empiar':
            pass
        # for sff:
        # https://www.ebi.ac.uk/em_static/emdb_sff/empiar_10087_c2_tomo02/empiar_10087_c2_tomo02.hff.gz
        # https://www.ebi.ac.uk/em_static/emdb_sff/empiar_10087_e64_tomo03/empiar_10087_e64_tomo03.hff.gz
        # https://www.ebi.ac.uk/em_static/emdb_sff/empiar_10070_b3talongmusc20130301/empiar_10070_b3talongmusc20130301.hff.gz

        # for maps
        # any API?

        # 1. 2 empiar VB entries with same ID
        

if __name__ == '__main__':
    args = parse_script_args()
    prepare_input_for_preprocessor(LIST_OF_ENTRY_IDS, args.output_dir)