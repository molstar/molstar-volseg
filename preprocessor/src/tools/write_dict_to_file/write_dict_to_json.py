import json
from pathlib import Path
from typing import Dict


def write_dict_to_json(d: Dict, filename: Path):
    with filename.open('w') as fp:
        json.dump(d, fp, indent=4)
