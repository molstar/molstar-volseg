import numpy as np
import zarr

from preprocessor.src.preprocessors.implementations.sff.preprocessor.constants import SEGMENTATION_DATA_GROUPNAME, VOLUME_DATA_GROUPNAME

def compute_chunk_size_based_on_data(arr: np.ndarray):
    pass

def get_volume_downsampling_from_zarr(
    downsampling_ratio: int,
    zarr_structure: zarr.hierarchy.Group) -> zarr.core.Array:
    root = zarr_structure
    arr: zarr.core.Array = root[VOLUME_DATA_GROUPNAME][downsampling_ratio]
    return arr
    
def get_segmentation_downsampling_from_zarr(
    downsampling_ratio: int,
    zarr_structure: zarr.hierarchy.Group,
    lattice_id: int) -> zarr.core.Array:
    root = zarr_structure
    arr: zarr.core.Array = root[SEGMENTATION_DATA_GROUPNAME][lattice_id][downsampling_ratio].grid
    return arr

def create_dataset_wrapper(
        zarr_group,
        data,
        name,
        shape,
        dtype,
        compressor,
        chunking_approach='auto'
    ) -> zarr.core.Array:

    if chunking_approach == 'auto':
        chunks = True
    elif chunking_approach == 'custom_function':
        chunks = compute_chunk_size_based_on_data(data)
    else:
        raise ValueError(f'Chunking approach arg value is invalid: {chunking_approach}')

    zarr_arr = zarr_group.create_dataset(
        data=data,
        name=name,
        shape=shape,
        dtype=dtype,
        compressor=compressor,
        chunks=chunks
    )

    return zarr_arr
