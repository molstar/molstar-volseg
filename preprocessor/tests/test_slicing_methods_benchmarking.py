from timeit import default_timer as timer
from tracemalloc import stop
from typing import Tuple
import unittest

from db.implementations.local_disk.local_disk_preprocessed_db import LocalDiskPreprocessedDb


class TestSlicingMethodsBenchmarking(unittest.IsolatedAsyncioTestCase):

    async def test(self):
        async def _compute_boxes_for_entry(db: LocalDiskPreprocessedDb, namespace, key):
            metadata = await db.read_grid_metadata(namespace, key)
            dims: Tuple = metadata.grid_dimensions()
            origin = (0, 0, 0)
            small_box = tuple([int(0.1 * x) for x in dims])
            medium_box = tuple([int(0.5 * x) for x in dims])
            large_box = tuple([x - 1 for x in dims])
            
            return (
                (origin, small_box),
                (origin, medium_box),
                (origin, large_box)
            )

        # method names
        test_suite_entries = [
            ('emdb', 'emd-1832'),
            ('emdb', 'emd-99999')
        ]

        test_suite_methods = [
            'zarr_colon',
            'zarr_gbs',
            'dask',
            'dask_from_zarr',
            'tensorstore'
        ]

        db = LocalDiskPreprocessedDb()

        for namespace, entry_id in test_suite_entries:
            print(f'ENTRY: {entry_id}')
            boxes = await _compute_boxes_for_entry(db, namespace, entry_id)
            for box in boxes:
                print(f'   BOX: {box}')
                for method in test_suite_methods:
                    start = timer()
                    slice_read = await db.read_slice(
                        namespace=namespace,
                        key=entry_id,
                        lattice_id=0,
                        down_sampling_ratio=1,
                        box=box,
                        mode=method
                    )
                    stop = timer()
                    print(f'      METHOD: {method} took {stop - start} seconds')