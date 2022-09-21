


import argparse
import subprocess
from pathlib import Path
from preprocessor.src.preprocessors.implementations.sff.preprocessor.constants import CSV_WITH_ENTRY_IDS_FILE, DEFAULT_DB_PATH, RAW_INPUT_FILES_DIR

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

def _preprocessor_wrapper(config: list[dict], args):
    for entry in config:
        # compile lst for preprocessor
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

        subprocess.call(lst)

def run_api(args):
    lst = [
        "python", "main.py",
        '--host', args.api_hostname,
        '--port', args.api_port
    ]
    subprocess.Popen(lst)

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
    config = csv_to_config_list_of_dicts(args.csv_with_entry_ids)
    updated_config = prepare_input_for_preprocessor(config=config, output_dir=args.raw_input_files_dir)
    _preprocessor_wrapper(updated_config, args)
    run_api(args)
    run_frontend(args)

if __name__ == '__main__':
    args = parse_script_args()
    download_files_build_and_deploy_db(args)