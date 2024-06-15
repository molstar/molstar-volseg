import argparse
import asyncio
import atexit
import multiprocessing
import shutil
from pathlib import Path

from cellstar_db.models import InputForBuildingDatabase
from cellstar_preprocessor.flows.constants import (
    DB_BUILDING_PARAMETERS_JSON,
    DEFAULT_DB_PATH,
    TEMP_ZARR_HIERARCHY_STORAGE_PATH,
)
from cellstar_preprocessor.preprocess import PreprocessorMode, main_preprocessor
from cellstar_preprocessor.tools.deploy_db.deploy_process_helper import (
    clean_up_processes,
)
from cellstar_preprocessor.tools.prepare_input_for_preprocessor.prepare_input_for_preprocessor import (
    json_to_list_of_inputs_for_building,
    prepare_input_for_preprocessor,
)

PROCESS_IDS_LIST = []


def parse_script_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--db_building_parameters_json",
        type=str,
        default=DB_BUILDING_PARAMETERS_JSON,
        help="",
    )
    # parser.add_argument('--raw_input_files_dir', type=Path, default=RAW_INPUT_FILES_DIR, help='dir with raw input files')
    parser.add_argument(
        "--db_path", type=str, default=DEFAULT_DB_PATH, help="path to db folder"
    )
    parser.add_argument(
        "--temp_zarr_hierarchy_storage_path",
        type=str,
        default=TEMP_ZARR_HIERARCHY_STORAGE_PATH,
        help="path to db working directory",
    )
    parser.add_argument(
        "--delete_existing_db",
        action="store_true",
        default=False,
        help="remove existing db directory",
    )
    args = parser.parse_args()
    return args


# common arguments
def _preprocessor_internal_wrapper(
    input_for_building: InputForBuildingDatabase, db_path: str, working_folder: str
):
    entry_id = input_for_building["entry_id"]
    print(f'Internal wrapper is adding {entry_id} to the database')
    quantize_downsampling_levels = None
    if "quantize_downsampling_levels" in input_for_building:
        quantize_downsampling_levels = []
        quantize_downsampling_levels = " ".join(
            str(item) for item in input_for_building["quantize_downsampling_levels"]
        )

    inputs = input_for_building["inputs"]
    input_pathes_list = [Path(i[0]) for i in inputs]
    input_kinds_list = [i[1] for i in inputs]

    asyncio.run(
        main_preprocessor(
            mode=PreprocessorMode.add,
            quantize_dtype_str=input_for_building.get("quantize_dtype_str"),
            quantize_downsampling_levels=quantize_downsampling_levels,
            force_volume_dtype=input_for_building.get("force_volume_dtype"),
            max_size_per_downsampling_lvl_mb=input_for_building.get(
                "max_size_per_downsampling_lvl_mb"
            ),
            min_size_per_downsampling_lvl_mb=input_for_building.get(
                "min_size_per_downsampling_lvl_mb", 5.0
            ),
            max_downsampling_level=input_for_building.get("max_downsampling_level"),
            min_downsampling_level=input_for_building.get("min_downsampling_level"),
            remove_original_resolution=input_for_building.get(
                "remove_original_resolution"
            ),
            entry_id=input_for_building.get("entry_id"),
            source_db=input_for_building.get("source_db"),
            source_db_id=input_for_building.get("source_db_id"),
            source_db_name=input_for_building.get("source_db_name"),
            working_folder=Path(working_folder),
            db_path=Path(db_path),
            input_paths=input_pathes_list,
            input_kinds=input_kinds_list,
        )
    )
    print(f'Internal wrapper have added {entry_id} to the database')
    

def _preprocessor_external_wrapper(
    arguments_list: list[tuple[InputForBuildingDatabase, str, str]]
):
    print('External preprocessor wrapper launched')
    with multiprocessing.Pool(multiprocessing.cpu_count()) as p:
        p.starmap(_preprocessor_internal_wrapper, arguments_list)

    p.join()


def build(args):
    if args.delete_existing_db and Path(args.db_path).exists():
        shutil.rmtree(args.db_path)

    if not args.temp_zarr_hierarchy_storage_path:
        temp_zarr_hierarchy_storage_path = (
            Path(TEMP_ZARR_HIERARCHY_STORAGE_PATH) / args.db_path
        )
    else:
        temp_zarr_hierarchy_storage_path = Path(args.temp_zarr_hierarchy_storage_path)

    # atexit.register(clean_up_temp_zarr_hierarchy_storage, temp_zarr_hierarchy_storage_path)

    # here it is removed
    if temp_zarr_hierarchy_storage_path.exists():
        # remove_temp_zarr_hierarchy_storage_folder(temp_zarr_hierarchy_storage_path)
        shutil.rmtree(temp_zarr_hierarchy_storage_path, ignore_errors=True)

    # clean_up_raw_input_files_dir(args.raw_input_files_dir)

    config = json_to_list_of_inputs_for_building(Path(args.db_building_parameters_json))
    print('JSON with building parameters was parsed')
    
    arguments_list = prepare_input_for_preprocessor(
        config=config,
        db_path=args.db_path,
        temp_zarr_hierarchy_storage_path=temp_zarr_hierarchy_storage_path,
    )
    print('Arguments list for preprocessor external wrapper was prepared')
    
    _preprocessor_external_wrapper(arguments_list)

    print('Preprocessor external wrapper preprocessed all entries')
    # TODO: this should be done only after everything is build
    shutil.rmtree(temp_zarr_hierarchy_storage_path, ignore_errors=True)


if __name__ == "__main__":
    # print("DEFAULT PORTS ARE TEMPORARILY SET TO 4000 and 8000, CHANGE THIS AFTERWARDS")
    atexit.register(clean_up_processes, PROCESS_IDS_LIST)
    args = parse_script_args()
    build(args)
