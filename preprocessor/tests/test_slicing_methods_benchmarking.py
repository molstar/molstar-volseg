import asyncio
from timeit import default_timer as timer
from tracemalloc import stop
from typing import Tuple
import unittest

from pathlib import Path

from db.implementations.local_disk.local_disk_preprocessed_db import LocalDiskPreprocessedDb
from preprocessor.src.tools.write_dict_to_file.write_dict_to_json import write_dict_to_json


class TestSlicingMethodsBenchmarking(unittest.IsolatedAsyncioTestCase):
    async def test(self):
        OVERWRITE_GOLD_STANDARD = False
        GOLD_STANDARD_FILENAME = Path('preprocessor/tests/performance_measurements/gold_standard.json')

        async def _compute_boxes_for_entry(db: LocalDiskPreprocessedDb, namespace, key):
            metadata = await db.read_metadata(namespace, key)
            dims: Tuple = metadata.grid_dimensions()
            origin = (0, 0, 0)
            small_box = tuple([int(0.1 * x) for x in dims])
            medium_box = tuple([int(0.5 * x) for x in dims])
            large_box = tuple([x - 1 for x in dims])
            
            boxes = (
                (origin, small_box),
                (origin, medium_box),
                (origin, large_box)
            )

            print(f'Boxes for {key}:')
            print(boxes)
            
            return boxes

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

        db = LocalDiskPreprocessedDb(Path('db'))

        d = {}
        for namespace, entry_id in test_suite_entries:
            print(f'ENTRY: {entry_id}')
            d[entry_id] = {}
            boxes = await _compute_boxes_for_entry(db, namespace, entry_id)
            for box in boxes:
                str_repr_of_box = f'{str(box[0])}, {str(box[1])}'
                d[entry_id][str_repr_of_box] = {}
                print(f'   BOX: {box}')
                for method in test_suite_methods:
                    start = timer()

                    with db.read(namespace=namespace, key=entry_id) as reader:
                        slice_read = await reader.read_slice(
                            lattice_id=0,
                            down_sampling_ratio=1,
                            box=box,
                            mode=method
                        )

                    stop = timer()
                    measurement = stop - start
                    d[entry_id][str_repr_of_box][method] = {
                        'measurement': measurement
                    }
                    print(f'      METHOD: {method} took {measurement} seconds')
                    if OVERWRITE_GOLD_STANDARD:
                        write_dict_to_json(d=d, filename=GOLD_STANDARD_FILENAME)

if __name__ == '__main__':
    t = TestSlicingMethodsBenchmarking()
    asyncio.run(t.test())