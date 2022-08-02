# TODO: suggest to switch default mode to zarr colon (faster)
from random import randint
import numpy as np
import pytest
from glob import glob
from pathlib import Path

from db.implementations.local_disk.local_disk_preprocessed_db import LocalDiskPreprocessedDb

KEYS = ['emd-9199']
BOX_CHOICES = ['random_static_region_small', 'random_static_region_big']
# DB_PATHES_FULL = glob('db_*/')
# DB_PATHES_FULL.remove('db_11\\')
# DB_PATHES_FULL.remove('db_12\\')
# DB_PATHS = DB_PATHES_FULL
DB_PATHS = ['db_quantized', 'db_not_quantized']

def generate_random_3d_point_coords(min: tuple[int, int, int], max: tuple[int, int, int]) -> tuple[int, int, int]:
    '''Both min and max are inclusive'''
    return (
        randint(min[0], max[0]),
        randint(min[1], max[1]),
        randint(min[2], max[2]),
    )

async def compute_random_static_box(db: LocalDiskPreprocessedDb, namespace: str, key: str, box: int):
    metadata = await db.read_metadata(namespace, key)
    dims: tuple = metadata.grid_dimensions()
    if key == 'emd-1832':
        box_size = box / 10
    else:
        box_size = box

    # grid dimensions = arr.shape, so for 64**3 grid entry, grid dimensions is 64,64,64
    # so we need to do -1
    # also we do -box_size to later add box_size
    max_coords = tuple([x - 1 for x in dims])
    max_coords_adjusted = tuple([x - box_size for x in max_coords])
    origin = (0, 0, 0)
    p1 = generate_random_3d_point_coords(origin, max_coords_adjusted)
    p2 = tuple([x + box_size for x in p1])
    assert (np.array(p2) <= np.array(max_coords)).all(), 'p2 exceeds max coords'
    box = (
        p1,
        p2
    )

    return box

async def compute_box_size_from_box_fraction(box_fraction: int, db: LocalDiskPreprocessedDb, namespace: str, key: str):
    metadata = await db.read_metadata(namespace, key)
    dims: tuple = metadata.grid_dimensions()
    origin = (0, 0, 0)
    max_coords = tuple([int(box_fraction * (x - 1)) for x in dims])

    box = (
        origin,
        max_coords
    )

    print(f'{box_fraction} box for {key}:')
    print(box)
    
    return box

@pytest.fixture(scope='function')
def aio_benchmark(benchmark):
    import asyncio
    import threading
    
    class Sync2Async:
        def __init__(self, coro, *args, **kwargs):
            self.coro = coro
            self.args = args
            self.kwargs = kwargs
            self.custom_loop = None
            self.thread = None
        
        def start_background_loop(self) -> None:
            asyncio.set_event_loop(self.custom_loop)
            self.custom_loop.run_forever()
        
        def __call__(self):
            evloop = None
            awaitable = self.coro(*self.args, **self.kwargs)
            try:
                evloop = asyncio.get_running_loop()
            except:
                pass
            if evloop is None:
                return asyncio.run(awaitable)
            else:
                if not self.custom_loop or not self.thread or not self.thread.is_alive():
                    self.custom_loop = asyncio.new_event_loop()
                    self.thread = threading.Thread(target=self.start_background_loop, daemon=True)
                    self.thread.start()
                
                return asyncio.run_coroutine_threadsafe(awaitable, self.custom_loop).result()
    
    def _wrapper(func, *args, **kwargs):
        if asyncio.iscoroutinefunction(func):
            benchmark(Sync2Async(func, *args, **kwargs))
        else:
            benchmark(func, *args, **kwargs)

    return _wrapper

@pytest.mark.parametrize("key", KEYS)
@pytest.mark.parametrize("box_choice", BOX_CHOICES)
@pytest.mark.parametrize("db_path", DB_PATHS)
@pytest.mark.asyncio
async def test_t(aio_benchmark, key, box_choice, db_path):
    @aio_benchmark
    async def _():
        # if db_path == 'db-ZIP//':
        #     db = LocalDiskPreprocessedDb(folder=Path(db_path), store_type='zip')
        # else:
        #     db = LocalDiskPreprocessedDb(folder=Path(db_path))
        db = LocalDiskPreprocessedDb(folder=Path(db_path), store_type='zip')

        if isinstance(box_choice, float):
            box = await compute_box_size_from_box_fraction(box_fraction=box_choice, db=db, namespace='emdb', key=key)
        elif isinstance(box_choice, str) and box_choice == 'random_static_region_small':
            box = await compute_random_static_box(db=db, namespace='emdb', key=key, box=127)
        elif isinstance(box_choice, str) and box_choice == 'random_static_region_big':
            box = await compute_random_static_box(db=db, namespace='emdb', key=key, box=299)

        with db.read(namespace='emdb', key=key) as reader:
            result = await reader.read_slice(
                lattice_id=0,
                down_sampling_ratio=1,
                box=box,
                mode='zarr_colon'
            )

        
    

# https://stackoverflow.com/questions/35110308/grouping-parametrized-benchmarks-with-pytest
# How to parametrize benchmarking function (not async, but yet)