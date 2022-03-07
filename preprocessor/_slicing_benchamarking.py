from pathlib import Path
from timeit import timeit
import zarr
import numpy as np
import dask.array as da
from db.implementations.local_disk.local_disk_preprocessed_db import LocalDiskPreprocessedDb

from asgiref.sync import async_to_sync

from preprocessor.implementations.sff_preprocessor import SEGMENTATION_DATA_GROUPNAME, VOLUME_DATA_GROUPNAME

MODES_LIST = [
    'np',
    'zarr_colon',
    'zarr_gbs',
    'dask',
    'dask_from_zarr',
    'tensorstore'
]

if __name__ == '__main__':
    db = LocalDiskPreprocessedDb()
    #     # continue from here: try timeit, try default_timer
    #     # https://stackoverflow.com/questions/7370801/how-to-measure-elapsed-time-in-python
    for mode in MODES_LIST:    
        slice_dict = async_to_sync(db.read_slice)('emdb', 'emd-1832', 0, 2, ((10,10,10), (25,25,25)), mode=mode)
        # timeit('print(z[:].tobytes())', number=1, globals=globals())
        # print(slice_dict)
