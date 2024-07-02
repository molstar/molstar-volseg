import ast
from pathlib import Path

import pandas as pd
import zarr
from cellstar_preprocessor.flows.zarr_methods import open_zarr

# PLAN:

# open CSV file
# find raw with that cellId
# get channel names
# all necessary info
# put to .attrs ['extra_data']
# access those attrs in extract_ometiff_metadata

# pandas.read_csv


def process_allencell_metadata_csv(
    path: Path, cell_id: int, intermediate_zarr_structure_path: Path
):
    zarr_structure: zarr.Group = open_zarr(intermediate_zarr_structure_path)

    df = pd.read_csv(str(path.resolve()))
    target_row = df[df["CellId"] == cell_id]
    name_dict_str = target_row["name_dict"][0]
    name_dict = ast.literal_eval(name_dict_str)
    # size of voxel in micrometers
    # taken not from ometiff, but from csv
    scale_micron_str = target_row["scale_micron"][0]
    scale_micron = ast.literal_eval(scale_micron_str)

    cell_stage = target_row["cell_stage"][0]

    zarr_structure.attrs["extra_data"] = {
        "name_dict": name_dict,
        # list with 3 float numbers in micrometers
        "scale_micron": scale_micron,
        "cell_stage": cell_stage,
    }
    print("Allencell metadata processed")
