import numpy as np
import zarr

from preprocessor.src.preprocessors.implementations.sff.preprocessor.constants import SEGMENTATION_DATA_GROUPNAME, VOLUME_DATA_GROUPNAME

def get_volume_downsampling_from_zarr(
    downsampling_ratio: int,
    zarr_structure: zarr.hierarchy.Group) -> zarr.core.Array:
    root = zarr_structure
    arr: zarr.core.Array = root[VOLUME_DATA_GROUPNAME][downsampling_ratio]
    return arr
    
def get_grid_segmentation_downsampling_from_zarr(
    downsampling_ratio: int,
    zarr_structure: zarr.hierarchy.Group,
    lattice_id: int) -> zarr.core.Array:
    root = zarr_structure
    arr: zarr.core.Array = root[SEGMENTATION_DATA_GROUPNAME][lattice_id][downsampling_ratio].grid
    return arr