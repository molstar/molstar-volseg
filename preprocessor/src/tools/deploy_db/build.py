


import argparse
import atexit
import multiprocessing
import os
import subprocess
from pathlib import Path
from preprocessor.main import remove_temp_zarr_hierarchy_storage_folder
from preprocessor.src.preprocessors.implementations.sff.preprocessor.constants import CSV_WITH_ENTRY_IDS_FILE, DEFAULT_DB_PATH, RAW_INPUT_FILES_DIR, TEMP_ZARR_HIERARCHY_STORAGE_PATH
from preprocessor.src.tools.deploy_db.deploy_process_helper import clean_up_processes, clean_up_temp_zarr_hierarchy_storage

from preprocessor.src.tools.prepare_input_for_preprocessor.prepare_input_for_preprocessor import csv_to_config_list_of_dicts, prepare_input_for_preprocessor

PROCESS_IDS_LIST = []
FOR_CLEANUP_TEMP_ZARR_HIERARCHY_STORAGE_PATH: Path

def parse_script_args():
    parser=argparse.ArgumentParser()
    parser.add_argument('--csv_with_entry_ids', type=Path, default=CSV_WITH_ENTRY_IDS_FILE, help='csv with entry ids and info for preprocessor')
    parser.add_argument('--raw_input_files_dir', type=Path, default=RAW_INPUT_FILES_DIR, help='dir with raw input files')
    parser.add_argument("--db_path", type=Path, default=DEFAULT_DB_PATH, help='path to db folder')
    parser.add_argument("--temp_zarr_hierarchy_storage_path", type=Path, help='path to db working directory')

    args=parser.parse_args()
    return args

def _preprocessor_internal_wrapper(entry: dict):
    lst = [
        "python", "preprocessor/main.py",
        "--db_path", entry['db_path'],    
        "--single_entry", entry['single_entry'],
        "--entry_id", entry['entry_id'],
        "--source_db", entry['source_db']
    ]

    if entry['force_volume_dtype']:
        lst.extend(['--force_volume_dtype', entry['force_volume_dtype']])
    
    if entry['quantization_dtype']:
        lst.extend(['--quantize_volume_data_dtype_str', entry['quantization_dtype']])

    if entry['temp_zarr_hierarchy_storage_path']:
        lst.extend(['--temp_zarr_hierarchy_storage_path', entry['temp_zarr_hierarchy_storage_path']])

    process = subprocess.Popen(lst)
    global PROCESS_IDS_LIST
    PROCESS_IDS_LIST.append(process.pid)

    return process.communicate()

def _preprocessor_external_wrapper(config: list[dict]):
    with multiprocessing.Pool(multiprocessing.cpu_count()) as p:
        result_iterator = p.map(_preprocessor_internal_wrapper, config)
        # print(123)
    
    p.join()

def build(args):
    if not args.temp_zarr_hierarchy_storage_path:
        temp_zarr_hierarchy_storage_path = TEMP_ZARR_HIERARCHY_STORAGE_PATH / args.db_path.name
    else:
        temp_zarr_hierarchy_storage_path = args.temp_zarr_hierarchy_storage_path

    global FOR_CLEANUP_TEMP_ZARR_HIERARCHY_STORAGE_PATH
    FOR_CLEANUP_TEMP_ZARR_HIERARCHY_STORAGE_PATH = temp_zarr_hierarchy_storage_path

    # here it is removed
    if temp_zarr_hierarchy_storage_path.exists():
        remove_temp_zarr_hierarchy_storage_folder(temp_zarr_hierarchy_storage_path)

    config = csv_to_config_list_of_dicts(args.csv_with_entry_ids)
    print('CSV was parsed')
    updated_config = prepare_input_for_preprocessor(config=config, output_dir=args.raw_input_files_dir,
        db_path=args.db_path,
        temp_zarr_hierarchy_storage_path=temp_zarr_hierarchy_storage_path)
    print('Input files have been downloaded')
    _preprocessor_external_wrapper(updated_config)

    # TODO: this should be done only after everything is build
    remove_temp_zarr_hierarchy_storage_folder(temp_zarr_hierarchy_storage_path)

if __name__ == '__main__':
    print("DEFAULT PORTS ARE TEMPORARILY SET TO 4000 and 8000, CHANGE THIS AFTERWARDS")
    atexit.register(clean_up_processes, PROCESS_IDS_LIST)
    atexit.register(clean_up_temp_zarr_hierarchy_storage, FOR_CLEANUP_TEMP_ZARR_HIERARCHY_STORAGE_PATH)
    args = parse_script_args()
    build(args)