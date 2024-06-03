import json
import subprocess
from pathlib import Path
from uuid import uuid4

import pytest

from vs_toolkit.tests.constants import DB_PATH_FOR_VS_TOOLKIT_TESTS, VS_TOOLKIT_PATH


def get_unique_cvsx_file_path():
    unique_name = str(uuid4())
    p = Path(f"vs_toolkit/tests/test_output/{unique_name}_results.zip")
    return p


def get_unique_json_query_params_path():
    unique_name = str(uuid4())
    return Path(
        f"vs_toolkit/tests/test_data/query_parameters/{unique_name}_query_parameters.json"
    )


def produce_cvsx(output_file_path: Path, json_with_query_params_path: Path):
    # This part is same everywhere
    commands_lst = [
        "python",
        str(VS_TOOLKIT_PATH.resolve()),
        "--db_path",
        str(DB_PATH_FOR_VS_TOOLKIT_TESTS.resolve()),
        "--out",
        str(output_file_path.resolve()),
        "--json-params-path",
        str(json_with_query_params_path.resolve()),
    ]
    subprocess.run(commands_lst)

    assert output_file_path.exists()
    assert output_file_path.is_file()

    # delete output file
    output_file_path.unlink()

    json_with_query_params_path.unlink()


def _create_json_with_query_params(
    query_params: dict, json_with_query_params_path: Path
):
    with json_with_query_params_path.open("w") as fp:
        json.dump(query_params, fp, indent=4)


query_params = [
    {
        "entry_id": "empiar-10070",
        "source_db": "empiar",
        "max_points": 100000,
        "detail_lvl": 9,
    },
    {"entry_id": "emd-1832", "source_db": "emdb"},
    {"entry_id": "idr-13457537", "source_db": "idr"},
    {
        "entry_id": "idr-13457537",
        "source_db": "idr",
        "channel_id": "Hyb probe",
        "time": 4,
    },
        {
        "entry_id": "emd-1273",
        "source_db": "emdb",
        "max_points": 100000000
    },
    {
        "entry_id": "empiar-11756",
        "source_db": "empiar",
        "segmentation_kind": "geometric-segmentation",
        "segmentation_id": "ribosomes",
        "max_points": 10000000,
    },
]


@pytest.mark.parametrize("query_params", query_params)
def test_query(query_params: dict):
    output_file_path = get_unique_cvsx_file_path()
    json_with_query_params_path = get_unique_json_query_params_path()
    _create_json_with_query_params(query_params, json_with_query_params_path)
    produce_cvsx(output_file_path, json_with_query_params_path)
