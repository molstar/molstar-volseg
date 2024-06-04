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
    # TODO: run as function
    # main_preprocessor
    # before that convert some arguments types used in main_preprocessor
    # input_for_building = defaultdict(str, input_for_building_raw)
    quantize_downsampling_levels = None
    if "quantize_downsampling_levels" in input_for_building:
        quantize_downsampling_levels = []
        quantize_downsampling_levels = " ".join(
            str(item) for item in input_for_building["quantize_downsampling_levels"]
        )

    # TODO: replace all absent values with None
    # if not 'quantize_dtype_str' in input_for_building:
    #     input_for_building['quantize_dtype_str'] = None
    # if input_for_building['quantize_dtype_str'] == 'u1':
    #     input_for_building['quantize_dtype_str'] = QuantizationDtype.u1
    # if input_for_building['quantize_dtype_str'] == 'u2':
    #     input_for_building['quantize_dtype_str'] = QuantizationDtype.u2

    # there is a list
    # each item is tuple
    # need to get two lists
    inputs = input_for_building["inputs"]
    input_pathes_list = [Path(i[0]) for i in inputs]
    input_kinds_list = [i[1] for i in inputs]
    # TODO: use starmap?
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

    # lst = [
    #     "python", "preprocessor/main.py",
    #     "--db_path", input,
    #     # "--single_entry", entry['single_entry'],
    #     "--entry_id", entry['entry_id'],
    #     "--source_db", entry['source_db'],
    #     "--source_db_id", entry['source_db_id'],
    #     "--source_db_name", entry['source_db_name']
    # ]

    # if entry['force_volume_dtype']:
    #     lst.extend(['--force_volume_dtype', entry['force_volume_dtype']])

    # if entry['quantization_dtype']:
    #     lst.extend(['--quantize_volume_data_dtype_str', entry['quantization_dtype']])

    # if entry['temp_zarr_hierarchy_storage_path']:
    #     lst.extend(['--temp_zarr_hierarchy_storage_path', entry['temp_zarr_hierarchy_storage_path']])

    # if entry['source_db'] == 'idr':
    #     lst.extend(['--ome_zarr_path', entry['ome_zarr_path']])

    # if entry['source_db'] == DB_NAME_FOR_OME_TIFF:
    #     lst.extend(['--ome_tiff_path', entry['ome_tiff_path']])

    # TODO: can run as function instead?
    # process = subprocess.Popen(lst)
    # global PROCESS_IDS_LIST
    # PROCESS_IDS_LIST.append(process.pid)

    # return process.communicate()


def _preprocessor_external_wrapper(
    arguments_list: list[tuple[InputForBuildingDatabase, str, str]]
):
    # need to provide that input:
    # input: InputForBuildingDatabase, db_path: str, working_folder: str
    # as list to starmap
    # arguments_list: list[tuple[InputForBuildingDatabase, str, str]] = []
    with multiprocessing.Pool(multiprocessing.cpu_count()) as p:
        # TODO: use starmap?
        p.starmap(_preprocessor_internal_wrapper, arguments_list)
        # print(123)

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

    # NOTE: this function should parse JSON to list[tuple[InputForBuildingDatabase]
    config = json_to_list_of_inputs_for_building(Path(args.db_building_parameters_json))

    # this function should create arguments list
    # arguments_list: list[tuple[InputForBuildingDatabase, str, str]]
    # from parsed list of InputForBuildingDatabase
    # and args.db_path and args temp_zarr_hierarchy_storage_path
    arguments_list = prepare_input_for_preprocessor(
        config=config,
        db_path=args.db_path,
        temp_zarr_hierarchy_storage_path=temp_zarr_hierarchy_storage_path,
    )

    # print('Input files have been downloaded')
    _preprocessor_external_wrapper(arguments_list)

    # TODO: this should be done only after everything is build
    shutil.rmtree(temp_zarr_hierarchy_storage_path, ignore_errors=True)


if __name__ == "__main__":
    # print("DEFAULT PORTS ARE TEMPORARILY SET TO 4000 and 8000, CHANGE THIS AFTERWARDS")
    atexit.register(clean_up_processes, PROCESS_IDS_LIST)
    args = parse_script_args()
    build(args)
