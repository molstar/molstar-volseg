from pathlib import Path
from typing import Tuple
import gemmi
import mrcfile
import numpy as np


def get_np_arr_from_gemmi(map_path: Path) -> np.ndarray:
    path = str(map_path.resolve())
    m = gemmi.read_ccp4_map(path)
    arr = np.array(m.grid)
    print(f'gemmi arr: dtype={arr.dtype}')
    return arr

def get_np_arr_from_mrcfile(map_path: Path) -> np.ndarray:
    path = str(map_path.resolve())
    m = mrcfile.open(path, mode='r')
    arr = m.data
    print(f'mrcfile arr: dtype={arr.dtype}')
    return arr

def compare_two_arrays(arr1, arr2):
    mask = arr1 == arr2
    reversed_mask = np.invert(mask)
    print(f'Not equal indices: {reversed_mask.nonzero()}')

def get_value_from_two_arrs(arr1, arr2, index: Tuple[int,int,int]):
    val_1 = arr1[index[0], index[1], index[2]]
    val_2 = arr2[index[0], index[1], index[2]]
    return val_1, val_2

if __name__ == '__main__':
    MAP_FILEPATH = Path('preprocessor/sample_volumes/emdb_sff/EMD-1832.map')
    arr1 = get_np_arr_from_gemmi(MAP_FILEPATH)
    arr2 = get_np_arr_from_mrcfile(MAP_FILEPATH)
    compare_two_arrays(arr1, arr2)
    # try to get value of (62, 31, 31) voxel
    indices = (62, 31, 31)
    gemmi_val, mrcfile_val = get_value_from_two_arrs(arr1, arr2, indices)
    print(f'indices: {indices}')
    print(f'gemmi_val {gemmi_val}')
    print(f'mrcfile_val {mrcfile_val}')

    indices = (1, 31, 32)
    gemmi_val, mrcfile_val = get_value_from_two_arrs(arr1, arr2, indices)
    print(f'indices: {indices}')
    print(f'gemmi_val {gemmi_val}')
    print(f'mrcfile_val {mrcfile_val}')
