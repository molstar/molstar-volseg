from pathlib import Path
from timeit import timeit
from typing import Tuple
import zarr
import numpy as np
import dask.array as da
from db.implementations.local_disk.local_disk_preprocessed_db import LocalDiskPreprocessedDb
from timeit import default_timer as timer
import tensorstore as ts

from asgiref.sync import async_to_sync

from preprocessor.implementations.sff_preprocessor import SEGMENTATION_DATA_GROUPNAME, VOLUME_DATA_GROUPNAME

MODES_LIST = [
    'zarr_colon',
    'zarr_gbs',
    'dask',
    'dask_from_zarr',
    'tensorstore'
]

CHUNK_SIZES = [25, 50, 100, 400]

TEMP_STORE_PATH = Path(__file__).parents[0] / 'temp' / 'benchmarking_zarr_structure'

def dummy_arr_benchmarking(shape: Tuple[int, int, int]):
    '''
    np - for 400*** grid - 1*10-5 sec
    zarr -||-              0.4 sec
    slicing with dask from_zarr is fastest, at least after 200*** grid
    '''
    np_arr = np.arange(shape[0] * shape[1] * shape[2]).reshape(shape[0], shape[1], shape[2])
    
    start_zarr_structure = timer()
    store: zarr.storage.DirectoryStore = zarr.DirectoryStore(TEMP_STORE_PATH)
    zarr_structure: zarr.hierarchy.group = zarr.group(store=store)

    # Group for storing zarr arrays
    dummy_group: zarr.hierarchy.group = zarr_structure.create_group('0')
    end_zarr_structure =  timer()

    # Group for storing dask arrays in zarr arrays storage
    dummy_group_for_dask_arr: zarr.hierarchy.group = zarr_structure.create_group('dask_group')


    print(f'CREATING ZARR STRUCTURE: {end_zarr_structure - start_zarr_structure}')
    for chunk_size in CHUNK_SIZES:
        stored_zarr_arr = dummy_group.create_dataset(
            chunk_size,
            shape=np_arr.shape,
            dtype=np_arr.dtype,
            chunks=(chunk_size, chunk_size, chunk_size)
        )
        stored_zarr_arr[...] = np_arr

        dask_arr = da.from_array(np_arr, chunks= (chunk_size, chunk_size, chunk_size))
        stored_dask_arr = dummy_group_for_dask_arr.create_dataset(
            chunk_size,
            shape=dask_arr.shape,
            dtype=dask_arr.dtype,
            chunks=(chunk_size, chunk_size, chunk_size)
        )
        # stores dask arr to zarr storage for dask arr
        dask_arr.store(stored_dask_arr)

    path: Path = Path(dummy_group.store.path).resolve() / dummy_group.path / 'stored_np_arr'
    zarr.save_array(path.resolve(), np_arr)

    print(f'SHAPE: {shape}')

    print(f'---ZARR arrs storing ZARR arrs')
    for arr_name, arr in dummy_group.arrays():
        print(f'CHUNK SIZE: {arr.chunks}')
        np_arr_slicing(np_arr)
        zarr_arr_slicing(arr)
        # too slow
        # zarr_arr_to_np_slicing(arr)
        zarr_arr_dask_slicing(arr)
        # too slow
        # stored_np_arr_slicing(path)
        zarr_arr_dask_from_zarr_slicing(arr)
        zarr_arr_tensorstore_slicing(arr)
    
    print(f'---ZARR arrs storing DASK arrs')
    for arr_name, arr in dummy_group_for_dask_arr.arrays():
        print(f'CHUNK SIZE: {arr.chunks}')
        np_arr_slicing(np_arr)
        zarr_arr_slicing(arr)
        # too slow
        # zarr_arr_to_np_slicing(arr)
        zarr_arr_dask_slicing(arr)
        # too slow
        # stored_np_arr_slicing(path)
        zarr_arr_dask_from_zarr_slicing(arr)
        zarr_arr_tensorstore_slicing(arr)
        dask_arr_stored_to_zarr_slicing(arr)

    store.rmdir()

def np_arr_slicing(np_arr: np.ndarray):
    start = timer()
    np_slice = np_arr[100:300, 100:300, 100:300]
    end = timer()
    print(f'np arr slicing: {end - start}')

def zarr_arr_slicing(zarr_arr: zarr.core.Array):
    start = timer()
    zarr_slice = zarr_arr[100:300, 100:300, 100:300]
    end = timer()
    print(f'zarr_arr arr slicing: {end - start}')

def zarr_arr_to_np_slicing(zarr_arr: zarr.core.Array):
    start = timer()
    np_arr = np.array(zarr_arr)
    np_arr_slice = np_arr[100:300, 100:300, 100:300]
    end = timer()
    print(f'zarr_arr converted to np arr slicing: {end - start}')

def zarr_arr_dask_slicing(zarr_arr: zarr.core.Array):
    start = timer()
    zd = da.from_array(zarr_arr, chunks=zarr_arr.chunks)
    dask_slice = zd[100:300, 100:300, 100:300]
    end = timer()
    print(f'zarr_arr arr slicing with dask: {end - start}')

def zarr_arr_dask_from_zarr_slicing(zarr_arr: zarr.core.Array):
    start = timer()
    zd = da.from_zarr(zarr_arr, chunks=zarr_arr.chunks)
    dask_slice = zd[100:300, 100:300, 100:300]
    end = timer()
    print(f'zarr_arr arr slicing with dask from_zarr: {end - start}')

def dask_arr_stored_to_zarr_slicing(zarr_arr: zarr.core.Array):
    # TODO: try https://stackoverflow.com/questions/61807955/efficient-way-of-storing-1tb-of-random-data-with-zarr
    # i.e. creating dask arr, storing to zarr storage, would it be faster to load dask arr from zarr storage
    # compared to doing da.from_zarr?

    start = timer()
    # this seems to slize by native Zarr slicing mechanism, treating zarr arr as zarr arr
    # dask_slice = zarr_arr[100:300, 100:300, 100:300]

    zd = da.from_zarr(zarr_arr, chunks=zarr_arr.chunks)
    dask_slice = zd[100:300, 100:300, 100:300]
    end = timer()
    print(f'dask arr slicing stored in zarr arr: {end - start}')
    

def zarr_arr_tensorstore_slicing(zarr_arr: zarr.core.Array):
    start = timer()
    path: Path = Path(zarr_arr.store.path).resolve() / zarr_arr.path
    store = ts.open(
        {
            'driver': 'zarr',
            'kvstore': {
                'driver': 'file',
                'path': str(path.resolve()),
            },
        },
        read=True
    ).result()
    sliced = store[100:300, 100:300, 100:300].read().result()
    end = timer()
    # print(store)
    print(f'zarr_arr arr slicing with tensorstore: {end - start}')

def stored_np_arr_slicing(path: Path):
    start_loading = timer()
    stored_np_arr = zarr.load(path.resolve())
    end_loading = timer()
    start_slicing = timer()
    np_slice = stored_np_arr[100:300, 100:300, 100:300]
    end_slicing = timer()
    print(f'stored np array total slicing+loading: {end_slicing - start_loading}')

def _get_sample_zarr_structure():
    PATH = Path('db') / 'emdb' / 'emd-1832'
    store: zarr.storage.DirectoryStore = zarr.DirectoryStore(PATH)
    # Re-create zarr hierarchy from opened store
    root: zarr.hierarchy.group = zarr.group(store=store)
    return root



if __name__ == '__main__':
    db = LocalDiskPreprocessedDb()
    # for mode in MODES_LIST:    
    #     slice_dict = async_to_sync(db.read_slice)('emdb', 'emd-1832', 0, 2, ((10,10,10), (25,25,25)), mode=mode)
        
    SHAPES_LIST = [
        # (100, 100, 100),
        # (200, 200, 200),
        (400, 400, 400),
        # (800, 800, 800) # freezes
    ]
    for shape in SHAPES_LIST:
        dummy_arr_benchmarking(shape=shape)
        # pass

    
