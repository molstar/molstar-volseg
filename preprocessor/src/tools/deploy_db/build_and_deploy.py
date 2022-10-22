


import argparse
import atexit
import multiprocessing
import os
import signal
import subprocess
from pathlib import Path
import sys
from typing import Optional
from preprocessor.main import remove_temp_zarr_hierarchy_storage_folder
from preprocessor.src.preprocessors.implementations.sff.preprocessor.constants import CSV_WITH_ENTRY_IDS_FILE, DEFAULT_DB_PATH, RAW_INPUT_FILES_DIR, TEMP_ZARR_HIERARCHY_STORAGE_PATH
import psutil
from preprocessor.src.tools.deploy_db.deploy_process_helper import clean_up_processes, clean_up_temp_zarr_hierarchy_storage

from preprocessor.src.tools.prepare_input_for_preprocessor.prepare_input_for_preprocessor import csv_to_config_list_of_dicts, prepare_input_for_preprocessor

PROCESS_IDS_LIST = []
FOR_CLEANUP_TEMP_ZARR_HIERARCHY_STORAGE_PATH: Optional[Path] = None
DEFAULT_HOST = '0.0.0.0'  # 0.0.0.0 = localhost
DEFAULT_PORT = 8000
DEFAULT_FRONTEND_PORT = 4000
DEPLOY_SCRIPT_PATH = str(Path("preprocessor/src/tools/deploy_db/build.py").resolve())
BUILD_SCRIPT_PATH = str(Path("preprocessor/src/tools/deploy_db/deploy.py").resolve())

def _path_resolver(path: Path) -> str:
    return str(path.resolve())

def parse_script_args():
    parser=argparse.ArgumentParser()
    parser.add_argument('--csv_with_entry_ids', type=Path, default=CSV_WITH_ENTRY_IDS_FILE, help='csv with entry ids and info for preprocessor')
    parser.add_argument('--raw_input_files_dir', type=Path, default=RAW_INPUT_FILES_DIR, help='dir with raw input files')
    parser.add_argument("--db_path", type=Path, default=DEFAULT_DB_PATH, help='path to db folder')
    parser.add_argument("--api_port", type=str, default=str(DEFAULT_PORT), help='default api port')
    parser.add_argument("--api_hostname", type=str, default=DEFAULT_HOST, help='default host')
    # NOTE: this will quantize everything (except u2/u1 thing), not what we need
    # parser.add_argument("--quantize_volume_data_dtype_str", action="store", choices=['u1', 'u2'])
    parser.add_argument("--frontend_port", type=str, default=str(DEFAULT_FRONTEND_PORT), help='default frontend port')
    parser.add_argument("--temp_zarr_hierarchy_storage_path", type=Path, help='path to db working directory')

    args=parser.parse_args()
    return args

def build_and_deploy_db(args):
    build_process = _build(args)
    deploy_process = _deploy(args)
    global PROCESS_IDS_LIST
    PROCESS_IDS_LIST.extend([build_process.pid, deploy_process.pid])
    return build_process, deploy_process

def _build(args):
    if not args.temp_zarr_hierarchy_storage_path:
        temp_zarr_hierarchy_storage_path = TEMP_ZARR_HIERARCHY_STORAGE_PATH / args.db_path.name
    else:
        temp_zarr_hierarchy_storage_path = args.temp_zarr_hierarchy_storage_path

    global FOR_CLEANUP_TEMP_ZARR_HIERARCHY_STORAGE_PATH
    FOR_CLEANUP_TEMP_ZARR_HIERARCHY_STORAGE_PATH = temp_zarr_hierarchy_storage_path

    build_lst = [
        "python", DEPLOY_SCRIPT_PATH,
        "--csv_with_entry_ids", _path_resolver(args.csv_with_entry_ids),
        "--raw_input_files_dir", _path_resolver(args.raw_input_files_dir),
        "--db_path", _path_resolver(args.db_path),
        "--temp_zarr_hierarchy_storage_path", _path_resolver(temp_zarr_hierarchy_storage_path)
    ]

    build_process = subprocess.Popen(build_lst)

    return build_process

def _deploy(args):
    deploy_lst = [
        "python", BUILD_SCRIPT_PATH,
        "--db_path", _path_resolver(args.db_path),
        "--api_port", args.api_port,
        "--api_hostname", args.api_hostname,
        "--frontend_port", args.frontend_port
    ]

    deploy_process = subprocess.Popen(deploy_lst)

    return deploy_process

if __name__ == '__main__':
    print("DEFAULT PORTS ARE TEMPORARILY SET TO 4000 and 8000, CHANGE THIS AFTERWARDS")
    atexit.register(clean_up_processes, PROCESS_IDS_LIST)
    atexit.register(clean_up_temp_zarr_hierarchy_storage, FOR_CLEANUP_TEMP_ZARR_HIERARCHY_STORAGE_PATH)
    args = parse_script_args()
    build_process, deploy_process = build_and_deploy_db(args)
    build_process.communicate()
    deploy_process.communicate()