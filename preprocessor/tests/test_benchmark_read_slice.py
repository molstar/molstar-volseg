# TODO: suggest to switch default mode to zarr colon (faster)
import pytest
from glob import glob
from pathlib import Path

from db.implementations.local_disk.local_disk_preprocessed_db import LocalDiskPreprocessedDb

async def compute_box_size_from_box_fraction(box_fraction: int, db: LocalDiskPreprocessedDb, namespace: str, key: str):
    metadata = await db.read_metadata(namespace, key)
    dims: tuple = metadata.grid_dimensions()
    origin = (0, 0, 0)
    max_coords = tuple([int(box_fraction * x) for x in dims])

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

@pytest.mark.parametrize("key", ['emd-1832', 'emd-99999'])
@pytest.mark.parametrize("box_fraction", [0.95])
@pytest.mark.parametrize("db_path", glob('db_*/'))
@pytest.mark.asyncio
async def test_t(aio_benchmark, key, box_fraction, db_path):
    @aio_benchmark
    async def _():
        db = LocalDiskPreprocessedDb(folder=Path(db_path))
        box = await compute_box_size_from_box_fraction(box_fraction=box_fraction, db=db, namespace='emdb', key=key)
        result = await db.read_slice(
            namespace='emdb',
            key=key,
            lattice_id=0,
            down_sampling_ratio=1,
            box=box,
            mode='zarr_colon'
        )

        
    

# https://stackoverflow.com/questions/35110308/grouping-parametrized-benchmarks-with-pytest
# How to parametrize benchmarking function (not async, but yet)