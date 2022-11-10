from typing import Optional
from preprocessor.main import remove_temp_zarr_hierarchy_storage_folder
import psutil
from pathlib import Path

def clean_up_processes(process_ids: list):
    print('CLEAN UP - killing all processes')
    print(f'PIDs to be killed {process_ids}')
    processes_list: list[psutil.Process] = []
    for process_id in process_ids:
        if psutil.pid_exists(process_id):
            processes_list.append(psutil.Process(process_id))

    # print([p.cmdline() for p in processes_list])
    
    
    for process in processes_list:
        for child in process.children(recursive=True):
            child.kill()
            print(f'Process killed by atexit: {child.cmdline()}')
        
        process.kill()
        print(f'Parent process killed by atexit: {process.cmdline()}')

def clean_up_temp_zarr_hierarchy_storage(temp_zarr_hierarchy_storage_path: Path):
    print(f'CLEANING TEMP ZARR HIERARCHY STRUCTURE DIR {temp_zarr_hierarchy_storage_path}')
    if temp_zarr_hierarchy_storage_path is not None and temp_zarr_hierarchy_storage_path.exists():
        print(f'Removing db working dir:{temp_zarr_hierarchy_storage_path}')
        remove_temp_zarr_hierarchy_storage_folder(temp_zarr_hierarchy_storage_path)

def _check_if_ssl_keyfile_and_certfile_provided(args):
    if args.ssl_keyfile and args.ssl_certfile:
        return True
    else:
        return False

def decide_port_number(args) -> str:
    # if development_mode == False, api_port arg is ignored
    if args.development_mode:
        return args.api_port
    elif _check_if_ssl_keyfile_and_certfile_provided(args):
        return '443'
    else:
        return '80'
