


import argparse
from pathlib import Path


def parse_script_args():
    parser=argparse.ArgumentParser()
    parser.add_argument('--csv_with-entry-ids')
    # TODO: add other args

    # parser.add_argument("--db_path", type=Path, default=DEFAULT_DB_PATH, help='path to db folder')
    # parser.add_argument("--raw_input_files_dir_path", type=Path, default=RAW_INPUT_FILES_DIR, help='path to directory with input files (maps and sff)')
    # parser.add_argument("--create_parametrized_dbs", action='store_true')
    # parser.add_argument("--quantize_volume_data_dtype_str", action="store", choices=['u1', 'u2'])
    # parser.add_argument('--single_entry', type=Path, help='path to folder with MAP and segmentation files')
    # parser.add_argument('--entry_id', type=str, help='entry id')
    # parser.add_argument('--source_db', type=str, help='source database name')
    # parser.add_argument('--force_volume_dtype', type=str, help='dtype of volume data to be used')
    args=parser.parse_args()
    return args

def _preprocessor_wrapper(config: list[dict]):
    pass

def deploy_db(args):
    pass
# run _preprocessor_wrapper
# run api similar to build_test_db.py
# run frontend similar to build_test_db.py

# if name main:
# parse args
# run deploy_db with args