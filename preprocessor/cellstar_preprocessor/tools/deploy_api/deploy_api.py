import argparse
import atexit
import os
import subprocess
from pathlib import Path
from sys import platform


from cellstar_db.file_system.constants import DEFAULT_PORT, DEFAULT_HOST
from cellstar_preprocessor.flows.constants import DEFAULT_DB_PATH
from cellstar_preprocessor.tools.deploy_db.deploy_process_helper import clean_up_processes

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
    parser.add_argument("--db_path", type=str, default=DEFAULT_DB_PATH, help='path to db folder')
    parser.add_argument("--api_port", type=str, help='api port', default=DEFAULT_PORT,)
    parser.add_argument("--api_hostname", type=str, default=DEFAULT_HOST, help='default host')
    
    args=parser.parse_args()
    return args

def _free_port(port_number: str):
    lst = ['killport', str(port_number)]
    subprocess.call(lst)

def run_api(args):
    tag = _get_git_tag()
    full_sha = _get_git_revision_hash()

    if os.path.isabs(args.db_path):
        db_path = Path(args.db_path)
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
    
    api_process = subprocess.Popen(lst, env=deploy_env, cwd='server/cellstar_server/')
    PROCESS_IDS_LIST.append(api_process.pid)
    print(f'API is running with args {vars(args)}')
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

