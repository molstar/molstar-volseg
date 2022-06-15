import pytest

from db.implementations.local_disk.local_disk_preprocessed_db import LocalDiskPreprocessedDb

@pytest.mark.parametrize("key", ['emd-1832', 'emd-99999'])
# TODO: box sizes should be computed using func we had from preprocessor\tests\test_slicing_methods_benchmarking.py
@pytest.mark.parametrize("box", [((10, 10, 10), (20, 20, 20)), ((10, 10, 10), (30, 30, 30))])
# TODO: downsampling ratios from metadata
@pytest.mark.parametrize("down_sampling_ratio", [1, 2])
@pytest.mark.asyncio
async def test_an_async_function(key, box, down_sampling_ratio):
    db = LocalDiskPreprocessedDb()
    result = await db.read_slice(
        namespace='emdb',
        key=key,
        lattice_id=0,
        down_sampling_ratio=down_sampling_ratio,
        box=box,
        mode='zarr_colon'
    )