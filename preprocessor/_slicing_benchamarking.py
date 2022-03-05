from pathlib import Path
import zarr
import numpy as np
import dask.array as da
from db.implementations.local_disk.local_disk_preprocessed_db import LocalDiskPreprocessedDb

from preprocessor.implementations.sff_preprocessor import SEGMENTATION_DATA_GROUPNAME, VOLUME_DATA_GROUPNAME

# TODO: create actual zarr hierarchy
_db = LocalDiskPreprocessedDb()
path: Path = _db.__path_to_object__('emdb', 'emd-1832')
store: zarr.storage.DirectoryStore = zarr.DirectoryStore(path)
box = ((2, 2, 2), (15,15,15))
root = zarr.group(store=store)

MODES_LIST = [
    'np',
    'zarr_colon',
    'zarr_gbs',
    'dask',
    'dask_from_zarr'
]

def read_slice(mode):
    if mode == 'np':
        # 1: numpy slicing (default)
        read_segm_arr: np.ndarray = root[SEGMENTATION_DATA_GROUPNAME][0]
        read_volume_arr: np.ndarray = root[VOLUME_DATA_GROUPNAME]
        segm_slice: np.ndarray = _db.__get_slice_from_three_d_arr(arr=read_segm_arr, box=box)
        volume_slice: np.ndarray = _db.__get_slice_from_three_d_arr(arr=read_volume_arr, box=box)
    elif mode =='zarr_colon':
        # 2: zarr slicing via : notation
        
        slice = arr[1:3, 1:3, 1:3]
    elif mode == 'zarr_gbs':
        # 3: zarr slicing via get_basic_selection and python slices
        root = zarr.group(store=store)
        arr = root.sgroup.sarr
        slice = arr.get_basic_selection(slice(1, 3), slice(1,3), slice(1,3))
    elif mode == 'dask':
        # 4: dask slicing: https://github.com/zarr-developers/zarr-python/issues/478#issuecomment-531148674
        # z = ...  # some zarr array
        # zd = da.from_array(z)
        # y = zd[::10]  # this is like a view - it's a deferred result, not computed until needed
    elif mode == 'dask_from_zarr':
        # 5: dask array from zarr? https://github.com/zarr-developers/zarr-python/issues/843
        # Using dask to slice the store with steps (dask.array.from_zarr(store)[::512])
        pass

if __name__ == '__main__':
    for mode in MODES_LIST:
        print(f'Mode: {mode}')
        timeit('print(z[:].tobytes())', number=1, globals=globals())  