


import argparse
import multiprocessing
import os
import subprocess
from pathlib import Path
from preprocessor.main import remove_temp_zarr_hierarchy_storage_folder
from preprocessor.src.preprocessors.implementations.sff.preprocessor.constants import CSV_WITH_ENTRY_IDS_FILE, DEFAULT_DB_PATH, RAW_INPUT_FILES_DIR, TEMP_ZARR_HIERARCHY_STORAGE_PATH

from preprocessor.src.tools.prepare_input_for_preprocessor.prepare_input_for_preprocessor import csv_to_config_list_of_dicts, prepare_input_for_preprocessor

from psutil import process_iter
from signal import SIGKILL

DEFAULT_HOST = '0.0.0.0'  # 0.0.0.0 = localhost
DEFAULT_PORT = 9000
DEFAULT_FRONTEND_PORT = 3000

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

    args=parser.parse_args()
    return args

def _free_port(port_number: str):
    lst = ['killport', str(port_number)]
    subprocess.call(lst)

def _preprocessor_internal_wrapper(entry: dict):
    lst = [
        "python", "preprocessor/main.py",
        "--db_path", args.db_path,    
        "--single_entry", entry['single_entry'],
        "--entry_id", entry['entry_id'],
        "--source_db", entry['source_db']
    ]

    if entry['force_volume_dtype']:
        lst.extend(['--force_volume_dtype', entry['force_volume_dtype']])
    
    if entry['quantization_dtype']:
        lst.extend(['--quantize_volume_data_dtype_str', entry['quantization_dtype']])

    subprocess.Popen(lst)

def _preprocessor_external_wrapper(config: list[dict]):
    with multiprocessing.Pool(multiprocessing.cpu_count()) as p:
        result_iterator = p.map(_preprocessor_internal_wrapper, config)
        # p.close
        # p.join()?

def run_api(args):
    deploy_env = {
        **os.environ,
        'DB_PATH': args.db_path,
        'HOST': args.api_hostname,
        'PORT': args.api_port
        }
    lst = [
        "python", "main.py"
    ]
    subprocess.Popen(lst, env=deploy_env)

def run_frontend(args):
    # TODO: check if this works in debug mode emd-1832
    subprocess.call(["yarn", "--cwd", "frontend"])
    subprocess.call(["yarn", "--cwd", "frontend", "build"])
    lst = [
        "serve",
        "-s", "frontend/build",
        "-l", str(args.frontend_port)
    ]
    # subprocess.Popen(lst)
    subprocess.call(lst)

def shut_down_ports(args):
    _free_port(args.frontend_port)
    _free_port(args.api_port)

def download_files_build_and_deploy_db(args):
    shut_down_ports(args)

    if TEMP_ZARR_HIERARCHY_STORAGE_PATH.exists():
        remove_temp_zarr_hierarchy_storage_folder(TEMP_ZARR_HIERARCHY_STORAGE_PATH)

    config = csv_to_config_list_of_dicts(args.csv_with_entry_ids)
    updated_config = prepare_input_for_preprocessor(config=config, output_dir=args.raw_input_files_dir, db_path=args.db_path)
    _preprocessor_external_wrapper(updated_config)

    remove_temp_zarr_hierarchy_storage_folder(TEMP_ZARR_HIERARCHY_STORAGE_PATH)
    run_api(args)
    run_frontend(args)

if __name__ == '__main__':
    args = parse_script_args()
    download_files_build_and_deploy_db(args)