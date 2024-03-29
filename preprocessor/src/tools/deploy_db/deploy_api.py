import argparse
import atexit
import os
import subprocess
from pathlib import Path
from preprocessor.main import remove_temp_zarr_hierarchy_storage_folder
from preprocessor.src.preprocessors.implementations.sff.preprocessor.constants import CSV_WITH_ENTRY_IDS_FILE, DEFAULT_DB_PATH, RAW_INPUT_FILES_DIR, TEMP_ZARR_HIERARCHY_STORAGE_PATH
from preprocessor.src.tools.deploy_db.build_and_deploy import DEFAULT_FRONTEND_PORT, DEFAULT_HOST, DEFAULT_PORT
from preprocessor.src.tools.deploy_db.deploy_process_helper import clean_up_processes
from sys import platform

PROCESS_IDS_LIST = []

# source: https://stackoverflow.com/a/21901260/13136429
def _get_git_revision_hash() -> str:
    return subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode('ascii').strip()

def _get_git_revision_short_hash() -> str:
    return subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode('ascii').strip()

def _get_git_tag() -> str:
    return subprocess.check_output(['git', 'describe']).decode('ascii').strip()

def parse_script_args():
    parser=argparse.ArgumentParser()
    parser.add_argument("--db_path", type=Path, default=DEFAULT_DB_PATH, help='path to db folder')
    parser.add_argument("--api_port", type=str, help='api port')
    parser.add_argument("--api_hostname", type=str, default=DEFAULT_HOST, help='default host')
    # NOTE: this will quantize everything (except u2/u1 thing), not what we need
    parser.add_argument("--frontend_port", type=str, default=str(DEFAULT_FRONTEND_PORT), help='default frontend port')
    
    args=parser.parse_args()
    return args

def _free_port(port_number: str):
    lst = ['killport', str(port_number)]
    subprocess.call(lst)

def run_api(args):
    tag = _get_git_tag()
    full_sha = _get_git_revision_hash()

    if os.path.isabs(args.db_path):
        db_path = args.db_path
    else:
        db_path = Path(os.getcwd()) / args.db_path
    deploy_env = {
        **os.environ,
        # check if relative path => then convert to absolute
        'DB_PATH': db_path,
        'HOST': args.api_hostname,
        'GIT_TAG': tag,
        'GIT_SHA': full_sha
        }

    if platform == "win32":
        deploy_env['DB_PATH'] = str(db_path.resolve())
        
    if args.api_port:
        deploy_env['PORT'] = args.api_port

    lst = [
        "python", "serve.py"
    ]
    # if not figure out how to pass full path
    api_process = subprocess.Popen(lst, env=deploy_env, cwd='server/')
    PROCESS_IDS_LIST.append(api_process.pid)

    return api_process

def deploy(args):
    if args.api_port:
        _free_port(args.api_port)
    else:
        _free_port(str(DEFAULT_PORT))
    api_process = run_api(args)
    api_process.communicate()

if __name__ == '__main__':
    atexit.register(clean_up_processes, PROCESS_IDS_LIST)
    args = parse_script_args()
    deploy(args)


