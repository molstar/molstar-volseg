# from preprocessor_old.main import remove_temp_zarr_hierarchy_storage_folder
import psutil


def clean_up_processes(process_ids: list):
    print("CLEAN UP - killing all processes")
    print(f"PIDs to be killed {process_ids}")
    processes_list: list[psutil.Process] = []
    for process_id in process_ids:
        if psutil.pid_exists(process_id):
            processes_list.append(psutil.Process(process_id))

    # print([p.cmdline() for p in processes_list])

    for process in processes_list:
        for child in process.children(recursive=True):
            child.kill()
            print(f"Process killed by atexit: {child.cmdline()}")

        process.kill()
        print(f"Parent process killed by atexit: {process.cmdline()}")


# def clean_up_temp_zarr_hierarchy_storage(temp_zarr_hierarchy_storage_path: Path):
#     print(f'CLEANING TEMP ZARR HIERARCHY STRUCTURE DIR {temp_zarr_hierarchy_storage_path}')
#     if temp_zarr_hierarchy_storage_path is not None and temp_zarr_hierarchy_storage_path.exists():
#         print(f'Removing db working dir:{temp_zarr_hierarchy_storage_path}')
#         # remove_temp_zarr_hierarchy_storage_folder(temp_zarr_hierarchy_storage_path)
#         shutil.rmtree(temp_zarr_hierarchy_storage_path, ignore_errors=True)

# def clean_up_raw_input_files_dir(raw_input_files_dir_path: Path):
#     print(f'CLEANING RAW INPUT FILES DIR {raw_input_files_dir_path}')
#     for path in raw_input_files_dir_path.glob("**/*"):
#         try:
#             if path.is_file():
#                 path.unlink()
#             elif path.is_dir():
#                 # NOTE: ignore errors?
#                 shutil.rmtree(path)
#         except Exception as e:
#             print(f'Problem with cleaning raw input files dir')
#             print(e)
