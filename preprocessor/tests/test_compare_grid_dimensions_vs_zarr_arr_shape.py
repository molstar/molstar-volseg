

from pathlib import Path
import unittest
from db.file_system.db import FileSystemDBReadContext

class TestSlicingMethodsBenchmarking(unittest.IsolatedAsyncioTestCase):
    async def test(self):
        db = FileSystemDBReadContext(folder=Path('db'))

        test_suite_entries = [
            ('emdb', 'emd-1832'),
            ('emdb', 'emd-99999')
        ]

        for namespace, entry_id in test_suite_entries:
            metadata = await db.read_metadata(namespace, entry_id)
            volume_downsamplings = metadata.volume_downsamplings()

            if entry_id != 'emd-99999':
                segmentation_downsamplings = metadata.segmentation_downsamplings(0)
                assert volume_downsamplings == segmentation_downsamplings, \
                    f'downsamplings are not equal for volume and segmentation: \
                        {volume_downsamplings} != {segmentation_downsamplings} \
                            for {namespace, entry_id}'
            
            with db.read(namespace=namespace, key=entry_id) as reader:
                for downsampling_ratio in volume_downsamplings:
                    arr_dict: dict = await reader.read(
                        lattice_id=0,
                        down_sampling_ratio=downsampling_ratio
                    )

                volume_arr = arr_dict['volume_arr']
                
                if downsampling_ratio == 1:
                    orig_grid_dimensions: list = metadata.grid_dimensions()    
                
                grid_dimensions: list = metadata.sampled_grid_dimensions(downsampling_ratio)

                if entry_id != 'emd-99999':
                    segmentation_arr = arr_dict['segmentation_arr']['category_set_ids']
                    self.assertEqual(volume_arr.shape, segmentation_arr.shape,
                        f'Not equal {volume_arr.shape, segmentation_arr.shape}'
                    )

                self.assertEqual(volume_arr.shape, tuple(grid_dimensions),
                    f'Not equal {volume_arr.shape, tuple(grid_dimensions)}'
                )
                
                if downsampling_ratio == 1:
                    self.assertEqual(volume_arr.shape, tuple(orig_grid_dimensions),
                        f'Not equal {volume_arr.shape, tuple(orig_grid_dimensions)}'
                    )

            



