

from argparse import Namespace
import argparse
from cellstar_preprocessor.flows.constants import DB_BUILDING_PARAMETERS_JSON, DEFAULT_DB_PATH, RAW_INPUT_DOWNLOAD_PARAMS_JSON, RAW_INPUT_FILES_DIR, TEMP_ZARR_HIERARCHY_STORAGE_PATH
from cellstar_preprocessor.tools.deploy_db.build import build
from cellstar_preprocessor.tools.deploy_db.download import download, store_db_building_params_to_json


def download_and_build(
    args: Namespace
):
    params = download(args)
    store_db_building_params_to_json(params, args)
    
    build(args) 
    
def parse_script_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--raw_input_download_params",
        type=str,
        default=RAW_INPUT_DOWNLOAD_PARAMS_JSON,
        help="",
    )
    parser.add_argument(
        "--raw_input_files_dir",
        type=str,
        default=RAW_INPUT_FILES_DIR,
        help="dir with raw input files",
    )
    parser.add_argument(
        "--db_building_params_json",
        type=str,
        default=DB_BUILDING_PARAMETERS_JSON,
        help="",
    )
    parser.add_argument(
        "--clean_existing_raw_inputs_folder", action="store_true", default=False
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

if __name__ == "__main__":
    args = parse_script_args()
    download_and_build(args)
