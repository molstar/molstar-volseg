from asgiref.sync import async_to_sync
import numpy as np

from pathlib import Path
from typing import Dict
from db.implementations.local_disk.local_disk_preprocessed_db import LocalDiskPreprocessedDb
from preprocessor.src.tools._write_fake_segmentation_to_sff import OUTPUT_FILEPATH as FAKE_SEGMENTATION_FILEPATH

from db.interface.i_preprocessed_db import IPreprocessedDb
from preprocessor.src.service.implementations import PreprocessorService
from preprocessor.src.preprocessors.implementations.sff.preprocessor.sff_preprocessor import SFFPreprocessor

RAW_INPUT_FILES_DIR = Path(__file__).parent / 'raw_input_files'

def obtain_paths_to_all_files(raw_input_files_dir: Path, hardcoded=True) -> Dict:
    '''
    Returns dict where keys = source names (e.g. EMDB), values = Lists of Dicts.
    In each (sub)Dict, Path objects to volume and segmentation files are provided along with entry name.
    Both files are located in one dir (name = entry name)
    ----
    Example:
    {'emdb': [
        {
            'id': emd-1832,
            'volume_file_path': Path(...),
            'segmentation_file_path': Path(...),
        },
        {
            ...
        },
    ]}
    '''
    d = {}
    # temp implementation
    if hardcoded == True:
        dummy_dict = {
            'emdb': [
                {
                    'id': 'emd-1832',
                    'volume_file_path': Path(__file__) / RAW_INPUT_FILES_DIR / 'emdb' / 'emd-1832' / 'EMD-1832.map',
                    'segmentation_file_path': Path(__file__) / RAW_INPUT_FILES_DIR / 'emdb' / 'emd-1832' / 'emd_1832.hff',
                },
                {
                    'id': 'fake-emd-1832',
                    'volume_file_path': Path(__file__) / RAW_INPUT_FILES_DIR / 'emdb' / 'emd-1832' / 'EMD-1832.map',
                    'segmentation_file_path': FAKE_SEGMENTATION_FILEPATH,
                }
                # {
                #     'id': 'empiar_10087_c2_tomo02',
                #     'volume_file_path': Path(__file__) / RAW_INPUT_FILES_DIR / 'emdb' / 'empiar_10087_c2_tomo02' / 'C2_tomo02.mrc',
                #     'segmentation_file_path': Path(__file__) / RAW_INPUT_FILES_DIR / 'emdb' / 'empiar_10087_c2_tomo02' / 'empiar_10087_c2_tomo02.hff',
                # },
                # {
                #     'id': 'empiar_10087_e64_tomo03',
                #     'volume_file_path': Path(__file__) / RAW_INPUT_FILES_DIR / 'emdb' / 'empiar_10087_e64_tomo03' / 'E64_tomo03.mrc',
                #     'segmentation_file_path': Path(__file__) / RAW_INPUT_FILES_DIR / 'emdb' / 'emd-empiar_10087_e64_tomo03' / 'empiar_10087_e64_tomo03.hff',
                # }
            ]
        }
        d = dummy_dict
    else:        
        # all ids should be lowercase!
        # TODO: later this dict can be compiled during batch raw file download, it should be easier than doing it like this
        for dir_path in raw_input_files_dir.iterdir():
            if dir_path.is_dir():               
                source_db = (dir_path.stem).lower()
                d[source_db] = []
                for subdir_path in dir_path.iterdir():
                    segmentation_file_path: Path = None

                    if subdir_path.is_dir():
                        content = sorted(subdir_path.glob('*'))
                        for item in content:
                            if item.is_file():
                                if item.suffix == '.hff':
                                    segmentation_file_path = item
                                if item.suffix == '.map' or item.suffix == '.ccp4' or item.suffix == '.mrc':
                                    volume_file_path: Path = item
                        d[source_db].append(
                            {
                                'id': (subdir_path.stem).lower(),
                                'volume_file_path': volume_file_path,
                                'segmentation_file_path': segmentation_file_path,
                            }
                        )
    return d

def preprocess_everything(db: IPreprocessedDb, raw_input_files_dir: Path) -> None:
    preprocessor_service = PreprocessorService([SFFPreprocessor()])
    files_dict = obtain_paths_to_all_files(raw_input_files_dir, hardcoded=False)
    for source_name, source_entries in files_dict.items():
        for entry in source_entries:
            segm_file_type = preprocessor_service.get_raw_file_type(entry['segmentation_file_path'])
            file_preprocessor = preprocessor_service.get_preprocessor(segm_file_type)
            if entry['segmentation_file_path'] == None:
                volume_force_dtype = np.uint8
            else:
                volume_force_dtype = np.float32
            processed_data_temp_path = file_preprocessor.preprocess(
                segm_file_path = entry['segmentation_file_path'],
                volume_file_path = entry['volume_file_path'],
                volume_force_dtype = volume_force_dtype
            )
            async_to_sync(db.store)(namespace=source_name, key=entry['id'], temp_store_path=processed_data_temp_path)

async def check_read_slice(db: LocalDiskPreprocessedDb):
    box = ((0, 0, 0), (10, 10, 10), (10, 10, 10))
    slice_emd_1832 = await db.read_slice(
        'emdb',
        'emd-1832',
        0,
        1,
        box
    )
    slice_emd_99999 = await db.read_slice(
        'emdb',
        'emd-99999',
        0,
        1,
        box
    )
    emd_1832_volume_slice = slice_emd_1832['volume_slice']
    emd_1832_segm_slice = slice_emd_1832['segmentation_slice']['category_set_ids']
    
    emd_99999_volume_slice = slice_emd_99999['volume_slice']

    print(f'volume slice_emd_1832 shape: {emd_1832_volume_slice.shape}, dtype: {emd_1832_volume_slice.dtype}')
    print(emd_1832_volume_slice)
    print(f'segmentation slice_emd_1832 shape: {emd_1832_segm_slice.shape}, dtype: {emd_1832_segm_slice.dtype}')
    print(emd_1832_segm_slice)
    print()
    print(f'volume slice_emd_99999 shape: {emd_99999_volume_slice.shape}, dtype: {emd_99999_volume_slice.dtype}')
    print(emd_99999_volume_slice)
    # print(slice)
    return {
        'slice_emd_1832': slice_emd_1832,
        'slice_emd_99999': slice_emd_99999
    }


if __name__ == '__main__':
    db = LocalDiskPreprocessedDb()
    db.remove_all_entries(namespace='emdb')
    preprocess_everything(db, RAW_INPUT_FILES_DIR)
    # uncomment to check read slice method
    # asyncio.run(check_read_slice(db))
    
    # event loop works, while async to sync returns Metadata class
    # https://stackoverflow.com/questions/44048536/python3-get-result-from-async-method
    # metadata = async_to_sync(db.read_metadata)(namespace='emdb', key='emd-1832')
    # print(metadata)

    # lat_ids = metadata.segmentation_lattice_ids()
    # segm_dwnsmplings = metadata.segmentation_downsamplings(lat_ids[0])
    # volume_downsamplings = metadata.volume_downsamplings()
    # origin = metadata.origin()
    # voxel_size = metadata.volume_downsamplings()
    # grid_dimensions = metadata.grid_dimensions()

    # print(lat_ids)
    # print(segm_dwnsmplings)
    # print(volume_downsamplings)
    # print(origin)
    # print(voxel_size)
    # print(grid_dimensions)