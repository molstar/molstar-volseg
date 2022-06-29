import pytest

from db.implementations.local_disk.local_disk_preprocessed_db import LocalDiskPreprocessedDb

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

@pytest.mark.asyncio
async def test_my_stuff(aio_benchmark):
    @aio_benchmark
    async def _():
        db = LocalDiskPreprocessedDb()

        test_suite_entries = [
            ('emdb', 'emd-1832'),
            ('emdb', 'emd-99999')
        ]
        for namespace, entry_id in test_suite_entries:
            await db.read_slice(
                namespace=namespace,
                key=entry_id,
                lattice_id=0,
                down_sampling_ratio=1,
                box=((10, 10, 10), (20, 20, 20)),
                mode='zarr_colon'
            )

# it runs the whole for loop and measures sum of all iterations 


