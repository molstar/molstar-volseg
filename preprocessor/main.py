import argparse
import asyncio
from pprint import pprint
import shutil
from asgiref.sync import async_to_sync
import numpy as np

from pathlib import Path
from numcodecs import Blosc
from typing import Dict
from db.implementations.local_disk.local_disk_preprocessed_db import LocalDiskPreprocessedDb
from preprocessor.params_for_storing_db import CHUNKING_MODES, COMPRESSORS
from preprocessor.src.service.implementations.preprocessor_service import PreprocessorService
from preprocessor.src.preprocessors.implementations.sff.preprocessor.constants import \
    OUTPUT_FILEPATH as FAKE_SEGMENTATION_FILEPATH, PARAMETRIZED_DBS_INPUT_PARAMS_FILEPATH, TEMP_ZARR_HIERARCHY_STORAGE_PATH

from db.interface.i_preprocessed_db import IPreprocessedDb
from preprocessor.src.preprocessors.implementations.sff.preprocessor.sff_preprocessor import SFFPreprocessor
from preprocessor.src.tools.convert_app_specific_segm_to_sff.convert_app_specific_segm_to_sff import convert_app_specific_segm_to_sff
from preprocessor.src.tools.remove_files_or_folders_by_pattern.remove_files_or_folders_by_pattern import remove_files_or_folders_by_pattern
from preprocessor.src.tools.write_dict_to_file.write_dict_to_json import write_dict_to_json
from preprocessor.src.tools.write_dict_to_file.write_dict_to_txt import write_dict_to_txt

RAW_INPUT_FILES_DIR = Path(__file__).parent / 'data/raw_input_files'
DEFAULT_DB_PATH = Path(__file__).parent.parent/'db' 
DEFAULT_QUANTIZE_DTYPE_STR = 'u1'
APPLICATION_SPECIFIC_SEGMENTATION_EXTENSIONS = ['.am', '.mod', '.seg', '.surf', '.stl']

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
    if hardcoded:
        dummy_dict = {
            'emdb': [
                {
                    'id': 'emd-1832',
                    'volume_file_path': Path(__file__) / RAW_INPUT_FILES_DIR / 'emdb' / 'emd-1832' / 'EMD-1832.map',
                    'segmentation_file_path': Path(
                        __file__) / RAW_INPUT_FILES_DIR / 'emdb' / 'emd-1832' / 'emd_1832.hff',
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
                                if item.suffix in APPLICATION_SPECIFIC_SEGMENTATION_EXTENSIONS:
                                    sff_segmentation_hff_file = convert_app_specific_segm_to_sff(input_file=item)
                                    segmentation_file_path = sff_segmentation_hff_file
                                elif item.suffix == '.hff':
                                    segmentation_file_path = item
                                elif item.suffix == '.map' or item.suffix == '.ccp4' or item.suffix == '.mrc':
                                    volume_file_path: Path = item
                        d[source_db].append(
                            {
                                'id': (subdir_path.stem).lower(),
                                'volume_file_path': volume_file_path,
                                'segmentation_file_path': segmentation_file_path,
                            }
                        )
    return d


def preprocess_everything(db: IPreprocessedDb, raw_input_files_dir: Path, params_for_storing: dict) -> None:
    preprocessor_service = PreprocessorService([SFFPreprocessor()])
    files_dict = obtain_paths_to_all_files(raw_input_files_dir, hardcoded=False)
    for source_name, source_entries in files_dict.items():
        for entry in source_entries:
            segm_file_type = preprocessor_service.get_raw_file_type(entry['segmentation_file_path'])
            file_preprocessor = preprocessor_service.get_preprocessor(segm_file_type)
            if entry['id'] == 'emd-99999' or entry['id'] == 'empiar-10070':
                volume_force_dtype = np.uint8
            else:
                volume_force_dtype = np.float32
            processed_data_temp_path = file_preprocessor.preprocess(
                segm_file_path=entry['segmentation_file_path'],
                volume_file_path=entry['volume_file_path'],
                volume_force_dtype=volume_force_dtype,
                params_for_storing=params_for_storing
            )
            async_to_sync(db.store)(namespace=source_name, key=entry['id'], temp_store_path=processed_data_temp_path)


async def check_read_slice(db: LocalDiskPreprocessedDb):
    box = ((0, 0, 0), (10, 10, 10), (10, 10, 10))
    
    with db.read(namespace='emdb', key='emd-99999') as reader:
        slice_emd_99999 = await reader.read_slice(
            lattice_id=0,
            down_sampling_ratio=1,
            box=box
        )

    with db.read(namespace='emdb', key='emd-1832') as reader:
        slice_emd_1832 = await reader.read_slice(
            lattice_id=0,
            down_sampling_ratio=1,
            box=box
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

async def check_read_meshes(db: LocalDiskPreprocessedDb):
    with db.read(namespace='empiar', key='empiar-10070') as reader:
        read_meshes_list = await reader.read_meshes(
            segment_id=15,
            detail_lvl=3
        )

    pprint(read_meshes_list)

    return read_meshes_list

def create_dict_of_input_params_for_storing(chunking_mode: list, compressors: list) -> dict:
    i = 1
    d = {}
    for mode in chunking_mode:
        for compressor in compressors:
            d[i] = {
                'chunking_mode': mode,
                'compressor': compressor,
                'store_type': 'directory'
            }
            i = i + 1
    
    return d

def remove_temp_zarr_hierarchy_storage_folder(path: Path):
    shutil.rmtree(path, ignore_errors=True)

def create_db(db_path: Path, params_for_storing: dict):
    new_db_path = Path(db_path)
    if new_db_path.is_dir() == False:
        new_db_path.mkdir()

    remove_temp_zarr_hierarchy_storage_folder(TEMP_ZARR_HIERARCHY_STORAGE_PATH)
    db = LocalDiskPreprocessedDb(new_db_path, params_for_storing['store_type'])
    db.remove_all_entries()
    preprocess_everything(db, RAW_INPUT_FILES_DIR, params_for_storing=params_for_storing)

def main():
    args = parse_script_args()
    if args.create_parametrized_dbs:
        # TODO: add quantize here too
        remove_files_or_folders_by_pattern('db_*/')
        storing_params_dict = create_dict_of_input_params_for_storing(
            chunking_mode=CHUNKING_MODES,
            compressors=COMPRESSORS
        )
        write_dict_to_txt(storing_params_dict, PARAMETRIZED_DBS_INPUT_PARAMS_FILEPATH)
        for db_id, param_set in storing_params_dict.items():
            create_db(Path(f'db_{db_id}'), params_for_storing=param_set)
    elif args.db_path:
        # print(args.quantize_volume_data_dtype_str)
        params_for_storing={
            'chunking_mode': 'auto',
            'compressor': Blosc(cname='lz4', clevel=5, shuffle=Blosc.SHUFFLE, blocksize=0),
            'store_type': 'zip'
        }
        if args.quantize_volume_data_dtype_str:
            params_for_storing['quantize_dtype_str'] = args.quantize_volume_data_dtype_str
        create_db(Path(args.db_path), params_for_storing=params_for_storing)
    else:
        raise ValueError('No db path is provided as argument')

def parse_script_args():
    parser=argparse.ArgumentParser()
    parser.add_argument("--db_path", type=Path, default=DEFAULT_DB_PATH, help='path to db folder')
    parser.add_argument("--create_parametrized_dbs", action='store_true')
    parser.add_argument("--quantize_volume_data_dtype_str", action="store", choices=['u1', 'u2'])
    args=parser.parse_args()
    return args

if __name__ == '__main__':
    main()


    # uncomment to check read slice method
    # asyncio.run(check_read_slice(db))

    # uncomment to check read_meshes method
    # asyncio.run(check_read_meshes(db))

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
