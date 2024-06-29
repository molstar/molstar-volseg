import argparse
import copy
import json
import multiprocessing
import os
import shutil
import ssl
import urllib.request
import zipfile
from pathlib import Path
from typing import TypedDict

from cellstar_db.models import PreprocessorParameters, RawInput

ssl._create_default_https_context = ssl._create_unverified_context

import ome_zarr
import ome_zarr.utils

# from _old.input_data_model import QuantizationDtype
from cellstar_db.models import (
    InputForBuildingDatabase,
    RawInputFileInfo,
    RawInputFilesDownloadParams,
)
from cellstar_preprocessor.flows.common import save_dict_to_json_file
from cellstar_preprocessor.flows.constants import (
    DB_BUILDING_PARAMETERS_JSON,
    RAW_INPUT_DOWNLOAD_PARAMS_JSON,
    RAW_INPUT_FILES_DIR,
)
from cellstar_db.models import InputKind
from cellstar_preprocessor.tools.gunzip.gunzip import gunzip


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
        "--db_building_parameters_json",
        type=str,
        default=DB_BUILDING_PARAMETERS_JSON,
        help="",
    )
    parser.add_argument(
        "--clean_existing_raw_inputs_folder", action="store_true", default=False
    )
    # parser.add_argument("--db_path", type=str, default=DEFAULT_DB_PATH, help='path to db folder')
    # parser.add_argument("--temp_zarr_hierarchy_storage_path", type=str, default=TEMP_ZARR_HIERARCHY_STORAGE_PATH, help='path to db working directory')
    # parser.add_argument("--delete_existing_db", action='store_true', default=False, help='remove existing db directory')
    args = parser.parse_args()
    return args


def _parse_raw_input_download_params_file(path: Path):
    with open(path.resolve(), "r", encoding="utf-8") as f:
        # reads into dict
        json_params: list[RawInputFilesDownloadParams] = json.load(f)

    return json_params


def _get_filename_from_uri(uri: str):
    # uri gonna be https://downloads.openmicroscopy.org/images/OME-TIFF/2016-06/tubhiswt-4D.zip
    parsed = uri.split("/")
    filename = parsed[-1]
    return filename


def _download(uri: str, final_path: Path, kind: InputKind):
    filename = _get_filename_from_uri(uri)
    # difference is that it should use final_path
    if kind == InputKind.omezarr:
        complete_path = final_path / filename
        if complete_path.exists():
            shutil.rmtree(complete_path, ignore_errors=True)

        # NOTE: using final_path here as it requires the directory inside
        # of which another directory will be created (idr-XXXX.zarr)
        ome_zarr.utils.download(uri, str(final_path.resolve()))
        return complete_path
    else:
        # TODO: download with pool
        try:
            # regular download
            # filename construct based on last component of uri
            complete_path = final_path / filename
            if complete_path.exists():
                if complete_path.is_dir():
                    shutil.rmtree(complete_path, ignore_errors=True)
                else:
                    complete_path.unlink()
            if not final_path.exists():
                final_path.mkdir(parents=True)
            urllib.request.urlretrieve(uri, str(complete_path.resolve()))
            return complete_path
        except Exception:
            print(f"uri: {uri}, final_path: {final_path}, kind: {kind}")


def _copy_file(uri: str, final_path: Path, kind: InputKind):
    filename = _get_filename_from_uri(uri)
    if not final_path.exists():
        #     shutil.rmtree(final_path)
        final_path.mkdir(parents=True)
    complete_path = final_path / filename
    # if omezarr - copy_tree
    # TODO: check if that would work for local omezarr
    if kind == InputKind.omezarr:
        shutil.copytree(uri, complete_path)
    else:
        shutil.copy2(uri, complete_path)

    return complete_path


# TODO: should return path to the first ometiff image
def _unzip_multiseries_ometiff_zip(zip_path: Path, kind: InputKind):
    directory_to_extract_to = zip_path.parent
    with zipfile.ZipFile(str(zip_path.resolve()), "r") as zip_ref:
        # where to extract
        # zip_ref.extractall(str(directory_to_extract_to.resolve()))
        # for elem in zip_ref.namelist() :
        #     zip_ref.extract(elem, str(directory_to_extract_to.resolve()))
        for zip_info in zip_ref.infolist():
            if zip_info.is_dir():
                continue
            zip_info.filename = os.path.basename(zip_info.filename)
            zip_ref.extract(zip_info, str(directory_to_extract_to.resolve()))

    zip_path.unlink()

    p: list[Path] = sorted(list(directory_to_extract_to.glob("*")))
    first_ometiff = p[0]
    return first_ometiff


# it should download file and copy file
def _get_file(input_file_info: RawInputFileInfo, final_path: Path) -> Path:
    resource = input_file_info["resource"]
    uri = resource["uri"]
    if resource["kind"] == "external":
        print(f"Downloading {uri}")
        complete_path = _download(
            input_file_info["resource"]["uri"], final_path, input_file_info["kind"]
        )
        return complete_path
    elif resource["kind"] == "local":
        print(f"Copying {uri}")
        complete_path = _copy_file(resource["uri"], final_path, input_file_info["kind"])
        # shutil.copy2(resource['uri'], final_path)
        return complete_path


class InputItemParams(TypedDict):
    # entry_folder_path: Path
    raw_input_file_info: RawInputFileInfo
    final_path: Path | None
    complete_path: Path | None
    raw_input_files_download_params: RawInputFilesDownloadParams
    preprocessor_parameters: PreprocessorParameters | None


def _get_file_pool_wrapper(params: InputItemParams):
    raw_input = params["raw_input_file_info"]
    final_path = params["final_path"]
    complete_path = _get_file(raw_input, final_path)
    updated_params: InputItemParams = copy.deepcopy(params)

    if complete_path.suffix == ".gz":
        complete_path = gunzip(complete_path)

    if complete_path.suffix == ".zip":
        # complete_path is path to zip file
        complete_path = _unzip_multiseries_ometiff_zip(complete_path, raw_input["kind"])

    updated_params["complete_path"] = complete_path
    return updated_params


def _create_db_building_params(updated_download_items: list[InputItemParams]):
    # check if there is no such thing i
    db_building_params: list[InputForBuildingDatabase] = []
    for i in updated_download_items:
        item = i["raw_input_files_download_params"]
        complete_path = i["complete_path"]
        kind = i["raw_input_file_info"]["kind"]
        # check if object exist in list
        target_item_idx = None
        for idx, p in enumerate(db_building_params):
            if p["entry_id"] == item["entry_id"] and p["source_db"] == p["source_db"]:
                target_item_idx = idx
                break

        single_input = RawInput(path=str(complete_path.resolve()), kind=kind)
        if target_item_idx == None:
            input_for_building_db: InputForBuildingDatabase = {
                "entry_id": item["entry_id"],
                "source_db": item["source_db"],
                "source_db_id": item["source_db_id"],
                "source_db_name": item["source_db_name"],
                "inputs": [single_input],
            }
            if "preprocessor_parameters" in i:
                for param in i["preprocessor_parameters"]:
                    input_for_building_db[param] = i["preprocessor_parameters"][param]

            db_building_params.append(input_for_building_db)

        else:
            f = list(
                filter(
                    lambda p: p["entry_id"] == item["entry_id"]
                    and p["source_db"] == p["source_db"],
                    db_building_params,
                )
            )
            assert (
                len(f) == 1
            ), "There must be a single item in the list of inputs for building db"
            # modify list item in place
            old_item = db_building_params[target_item_idx]
            old_inputs = old_item["inputs"]
            old_inputs.append(single_input)
            old_item["inputs"] = old_inputs
            db_building_params[target_item_idx] = old_item
            new_inputs_content = db_building_params[target_item_idx]["inputs"]
            print(f"New inputs content: {new_inputs_content} for ")

    return db_building_params


def download(args: argparse.Namespace):
    db_building_params: list[InputForBuildingDatabase] = []

    raw_unput_files_dir = Path(args.raw_input_files_dir)
    if args.clean_existing_raw_inputs_folder:
        for path in raw_unput_files_dir.glob("**/*"):
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                shutil.rmtree(path, ignore_errors=True)

    download_params_file_path = Path(args.raw_input_download_params)
    download_params = _parse_raw_input_download_params_file(download_params_file_path)

    download_items: list[InputItemParams] = []

    for item in download_params:
        entry_folder_path = raw_unput_files_dir / item["source_db"] / item["entry_id"]
        for raw_input in item["inputs"]:
            d: InputItemParams = {
                "raw_input_file_info": raw_input,
                "final_path": entry_folder_path / raw_input["kind"],
                "raw_input_files_download_params": item,
            }

            if "preprocessor_parameters" in raw_input:
                d["preprocessor_parameters"] = raw_input["preprocessor_parameters"]

            download_items.append(d)

    with multiprocessing.Pool(multiprocessing.cpu_count()) as p:
        updated_download_items = p.map(_get_file_pool_wrapper, download_items)

    del download_items

    p.join()

    # 2. separate function for creating db_building_params
    db_building_params = _create_db_building_params(updated_download_items)

    return db_building_params


def store_db_building_params_to_json(
    db_building_params: list[InputForBuildingDatabase], args: argparse.Namespace
):
    filename = Path(args.db_building_parameters_json).name
    folder = Path(args.db_building_parameters_json).parent
    save_dict_to_json_file([d.dict() for d in db_building_params], filename, folder)