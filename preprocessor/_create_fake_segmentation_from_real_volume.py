from pathlib import Path
import numpy as np
from preprocessor.implementations.sff_preprocessor import SFFPreprocessor

# toy for now
# TODO:
MAP_FILEPATH = ''

def create_fake_segmentation_from_real_volume(volume_filepath: Path) -> np.ndarray:
    prep = SFFPreprocessor()
    volume_grid: np.ndarray = prep.read_and_normalize_volume_map()
    # empty segm grid
    segmentation_grid: np.ndarray = np.full(list(volume_grid.shape), np.int32)
    assert segmentation_grid.dtype == np.int32
    assert segmentation_grid.shape == volume_grid.shape


def get_mask(center_coords: Tuple[int, int, int], radius: int, arr: np.ndarray):
    cx, cy, cz = center_coords
    sx, sy, sz = arr.shape
    x, y, z = np.ogrid[:sx, :sy, :sz]
    mask = (x - cx)**2 + (y - cy)**2 + (z - cz)**2 <= radius**2
    return mask

    # TODO: get indices (coords) instead of bool mask to be able to exclude those indices from list
    # of all coords of voxels whose values are > 2sigma 



    






