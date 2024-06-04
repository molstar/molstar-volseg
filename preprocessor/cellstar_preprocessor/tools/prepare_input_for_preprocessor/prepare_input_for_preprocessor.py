# e.g. emd-1832 or emd_1832
import json
from pathlib import Path

from cellstar_db.models import InputForBuildingDatabase

STATIC_INPUT_FILES_DIR = Path("temp/v2_temp_static_entry_files_dir")

TEST_RAW_INPUT_FILES_DIR = Path("temp/test_raw_input_files_dir")


def json_to_list_of_inputs_for_building(json_path: Path):
    with open(json_path.resolve(), "r", encoding="utf-8") as f:
        # reads into list
        read_json: list[InputForBuildingDatabase] = json.load(f)
    return read_json


def prepare_input_for_preprocessor(
    config: list[InputForBuildingDatabase],
    db_path: str,
    temp_zarr_hierarchy_storage_path: str,
) -> list[dict]:
    arguments_list = []
    for input in config:
        arguments_list.append(
            (input, Path(db_path), Path(temp_zarr_hierarchy_storage_path))
        )
    return arguments_list
