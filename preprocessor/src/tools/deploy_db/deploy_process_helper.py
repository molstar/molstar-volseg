from preprocessor.main import remove_temp_zarr_hierarchy_storage_folder
import psutil
from pathlib import Path

def clean_up_processes(process_ids: list):
    print('CLEAN UP - killing all processes')
    processes_list: list[psutil.Process] = []
    for process_id in process_ids:
        processes_list.append(psutil.Process(process_id))

    # print([p.cmdline() for p in processes_list])
    
    
    for process in processes_list:
        for child in process.children(recursive=True):
            child.kill()
            # print(f'Process killed by atexit: {child.cmdline()}')
        
        process.kill()
        # print(f'Parent process killed by atexit: {process.cmdline()}')

def clean_up_temp_zarr_hierarchy_storage(temp_zarr_hierarchy_storage_path: Path):
    if temp_zarr_hierarchy_storage_path.exists():
        print(f'Removing db working dir:{temp_zarr_hierarchy_storage_path}')
        remove_temp_zarr_hierarchy_storage_folder(temp_zarr_hierarchy_storage_path)
