from pathlib import Path

import numpy as np
import zarr
from cellstar_db.models import DownsamplingLevelInfo


def _compute_chunk_size_based_on_data(arr: np.ndarray) -> tuple[int, int, int]:
    shape: tuple = arr.shape
    chunks = tuple([int(i / 4) if i > 4 else i for i in shape])
    return chunks


def create_dataset_wrapper(
    zarr_group: zarr.Group,
    data,
    name,
    shape,
    dtype,
    params_for_storing: dict,
    is_empty=False,
) -> zarr.Array:
    compressor = params_for_storing.compressor
    chunking_mode = params_for_storing.chunking_mode

    if chunking_mode == "auto":
        chunks = True
    elif chunking_mode == "custom_function":
        chunks = _compute_chunk_size_based_on_data(data)
    elif chunking_mode == "false":
        chunks = False
    else:
        raise ValueError(f"Chunking approach arg value is invalid: {chunking_mode}")
    if not is_empty:
        zarr_arr = zarr_group.create_dataset(
            data=data,
            name=name,
            shape=shape,
            dtype=dtype,
            compressor=compressor,
            chunks=chunks,
        )
    else:
        zarr_arr = zarr_group.create_dataset(
            name=name, shape=shape, dtype=dtype, compressor=compressor, chunks=chunks
        )

    return zarr_arr


# TODO: refactor to internal data
def get_downsamplings(data_group: zarr.Group) -> list[DownsamplingLevelInfo]:
    downsamplings = []
    for gr_name, gr in data_group.groups():
        downsamplings.append(gr_name)
        downsamplings = sorted(downsamplings)

    # convert to ints
    downsamplings = sorted([int(x) for x in downsamplings])
    downsampling_info_list: list[DownsamplingLevelInfo] = []
    for downsampling in downsamplings:
        info: DownsamplingLevelInfo = DownsamplingLevelInfo.parse_obj(
            {"available": True, "level": downsampling}
        )
        downsampling_info_list.append(info)

    return downsampling_info_list


def open_zarr_zip(path: Path) -> zarr.Group:
    store = zarr.ZipStore(path=path, compression=0, allowZip64=True, mode="r")
    # Re-create zarr hierarchy from opened store
    root: zarr.Group = zarr.group(store=store)
    return root


def open_zarr(path: Path) -> zarr.Group:
    store: zarr.storage.DirectoryStore = zarr.DirectoryStore(str(path))
    # Re-create zarr hierarchy from opened store
    root: zarr.Group = zarr.group(store=store)
    return root
