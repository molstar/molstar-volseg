import zarr
import argparse
import asyncio
import logging
from pprint import pprint
import shutil
from asgiref.sync import async_to_sync
import numpy as np
import numcodecs
from PIL import ImageColor

from pathlib import Path
from numcodecs import Blosc
from typing import Dict, Optional, Union
from db.file_system.db import FileSystemVolumeServerDB
from db.file_system.constants import ANNOTATION_METADATA_FILENAME, GRID_METADATA_FILENAME, SEGMENTATION_DATA_GROUPNAME, VOLUME_DATA_GROUPNAME
from preprocessor.params_for_storing_db import CHUNKING_MODES, COMPRESSORS
from preprocessor.src.service.implementations.preprocessor_service import PreprocessorService
from preprocessor.src.preprocessors.implementations.sff.preprocessor.constants import \
    APPLICATION_SPECIFIC_SEGMENTATION_EXTENSIONS, DEFAULT_DB_PATH, OUTPUT_FILEPATH as FAKE_SEGMENTATION_FILEPATH, PARAMETRIZED_DBS_INPUT_PARAMS_FILEPATH, RAW_INPUT_FILES_DIR, TEMP_ZARR_HIERARCHY_STORAGE_PATH

from db.protocol import VolumeServerDB
from preprocessor.src.preprocessors.implementations.sff.preprocessor.sff_preprocessor import SFFPreprocessor
from preprocessor.src.tools.convert_app_specific_segm_to_sff.convert_app_specific_segm_to_sff import convert_app_specific_segm_to_sff
from preprocessor.src.tools.remove_files_or_folders_by_pattern.remove_files_or_folders_by_pattern import remove_files_or_folders_by_pattern
from preprocessor.src.tools.write_dict_to_file.write_dict_to_json import write_dict_to_json
from preprocessor.src.tools.write_dict_to_file.write_dict_to_txt import write_dict_to_txt

OME_ZARR_DEFAULT_PATH = Path('sample_ome_zarr_from_ome_zarr_py_docs/6001240.zarr')

def obtain_paths_to_single_entry_files(input_files_dir: Path) -> Dict:
    d = {}
    segmentation_file_path: Path = None
    volume_file_path: Optional[Path] = None

    if input_files_dir.is_dir():
        content = sorted(input_files_dir.glob('*'))
        for item in content:
            if item.is_file():
                if item.suffix in APPLICATION_SPECIFIC_SEGMENTATION_EXTENSIONS:
                    sff_segmentation_hff_file = convert_app_specific_segm_to_sff(input_file=item)
                    segmentation_file_path = sff_segmentation_hff_file
                elif item.suffix == '.hff':
                    segmentation_file_path = item
                elif item.suffix == '.map' or item.suffix == '.ccp4' or item.suffix == '.mrc':
                    volume_file_path = item
        if volume_file_path == None:
            raise Exception('Volume file not found')
            
        d = {
                'id': (input_files_dir.stem).lower(),
                'volume_file_path': volume_file_path,
                'segmentation_file_path': segmentation_file_path,
            }

        return d
    else:
        raise Exception('input files dir path is not directory')


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
                    single_entry_dict = obtain_paths_to_single_entry_files(input_files_dir=subdir_path)        
                    d[source_db].append(single_entry_dict)
    return d


async def preprocess_everything(db: VolumeServerDB, raw_input_files_dir: Path, params_for_storing: dict, temp_zarr_hierarchy_storage_path: Path) -> None:
    preprocessor_service = PreprocessorService([SFFPreprocessor(temp_zarr_hierarchy_storage_path)])
    files_dict = obtain_paths_to_all_files(raw_input_files_dir, hardcoded=False)
    for source_name, source_entries in files_dict.items():
        for entry in source_entries:
            # check if entry exists
            if await db.contains(namespace=source_name, key=entry['id']):
                await db.delete(namespace=source_name, key=entry['id'])

            segm_file_type = preprocessor_service.get_raw_file_type(entry['segmentation_file_path'])
            file_preprocessor = preprocessor_service.get_preprocessor(segm_file_type)
            # for now np.float32 by default, after mrcfile guys will confirm that map is read according to mode - could be None
            processed_data_temp_path = file_preprocessor.preprocess(
                segm_file_path=entry['segmentation_file_path'],
                volume_file_path=entry['volume_file_path'],
                volume_force_dtype=None,
                params_for_storing=params_for_storing,
                entry_id=entry['id'],
                source_db_id=entry['id'],
                source_db_name=source_name
            )
            await db.store(namespace=source_name, key=entry['id'], temp_store_path=processed_data_temp_path)

async def preprocess_single_entry(db: VolumeServerDB, input_files_dir: Path, params_for_storing: dict, entry_id: str, source_db: str, force_volume_dtype: Union[str, None],
        temp_zarr_hierarchy_storage_path: Path,
        source_db_id: str,
        source_db_name: str) -> None:
    preprocessor_service = PreprocessorService([SFFPreprocessor(temp_zarr_hierarchy_storage_path=temp_zarr_hierarchy_storage_path)])
    if await db.contains(namespace=source_db, key=entry_id):
        await db.delete(namespace=source_db, key=entry_id)

    files_dict = obtain_paths_to_single_entry_files(input_files_dir)

    segm_file_type = preprocessor_service.get_raw_file_type(files_dict['segmentation_file_path'])
    file_preprocessor = preprocessor_service.get_preprocessor(segm_file_type)

    if force_volume_dtype is not None:
        try:
            force_volume_dtype = np.dtype(force_volume_dtype)
        except Exception as e:
            logging.error(e, stack_info=True, exc_info=True)
            raise e

    processed_data_temp_path = file_preprocessor.preprocess(
        segm_file_path=files_dict['segmentation_file_path'],
        volume_file_path=files_dict['volume_file_path'],
        volume_force_dtype=force_volume_dtype,
        params_for_storing=params_for_storing,
        entry_id=entry_id,
        source_db_id=source_db_id,
        source_db_name=source_db_name
    )
    await db.store(namespace=source_db, key=entry_id, temp_store_path=processed_data_temp_path)
    
async def check_read_slice(db: VolumeServerDB):
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

async def check_read_meshes(db: VolumeServerDB):
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

async def create_db(db_path: Path, params_for_storing: dict,
    raw_input_files_dir_path: Path,
    temp_zarr_hierarchy_storage_path: Path):
    new_db_path = Path(db_path)
    if new_db_path.is_dir() == False:
        new_db_path.mkdir()

    remove_temp_zarr_hierarchy_storage_folder(temp_zarr_hierarchy_storage_path)
    db = FileSystemVolumeServerDB(new_db_path, params_for_storing['store_type'])
    # db.remove_all_entries()
    await preprocess_everything(db, raw_input_files_dir_path, params_for_storing=params_for_storing,
        temp_zarr_hierarchy_storage_path=temp_zarr_hierarchy_storage_path)

async def add_entry_to_db(
        db_path: Path,
        params_for_storing: dict,
        input_files_dir: Path,
        entry_id: str,
        source_db: str,
        force_volume_dtype: Union[str, None],
        temp_zarr_hierarchy_storage_path: Path,
        source_db_id: str,
        source_db_name: str):
    '''
    By default, initializes db with store_type = "zip"
    '''
    new_db_path = Path(db_path)
    if new_db_path.is_dir() == False:
        new_db_path.mkdir()

    # NOTE: with this multiprocessing in deployement script may not work, so commented
    # remove_temp_zarr_hierarchy_storage_folder(TEMP_ZARR_HIERARCHY_STORAGE_PATH)
    db = FileSystemVolumeServerDB(new_db_path, store_type='zip')
    await preprocess_single_entry(
        db=db,
        input_files_dir=input_files_dir,
        params_for_storing=params_for_storing,
        entry_id=entry_id,
        source_db=source_db,
        force_volume_dtype=force_volume_dtype,
        temp_zarr_hierarchy_storage_path=temp_zarr_hierarchy_storage_path,
        source_db_id=source_db_id,
        source_db_name=source_db_name
        )

def _compose_voxel_sizes_in_downsamplings_dict(ome_zarr_root):
    root_zattrs = ome_zarr_root.attrs
    multiscales = root_zattrs["multiscales"]
    datasets_meta = multiscales[0]["datasets"]

    labels_datasets_meta = ome_zarr_root['labels'][0].attrs['multiscales'][0]["datasets"]

    d = {}
    
    for index, level in enumerate(datasets_meta):
        scale_arr = level['coordinateTransformations'][0]['scale']
        # check if multiscales in labels are the same
        assert scale_arr == labels_datasets_meta[index]['coordinateTransformations'][0]['scale']
        # no channel, *micrometers to angstroms
        scale_arr = scale_arr[1:]
        scale_arr = [i*10000 for i in scale_arr]
        # x and z swapped
        d[level['path']] = (
            scale_arr[2],
            scale_arr[1],
            scale_arr[0]
        )

    return d

# NOTE: one volume_force_dtype for all resolutions
def extract_ome_zarr_metadata(our_zarr_structure: zarr.hierarchy.group, volume_force_dtype: np.dtype,
        source_db_id: str,
        source_db_name: str,
        ome_zarr_root: zarr.hierarchy.group) -> dict:
    root = our_zarr_structure
    
    volume_downsamplings = sorted(root[VOLUME_DATA_GROUPNAME].array_keys())
    # convert to ints
    volume_downsamplings = sorted([int(x) for x in volume_downsamplings])

    mean_dict = {}
    std_dict = {}
    max_dict = {}
    min_dict = {}
    grid_dimensions_dict = {}

    for arr_name, arr in root[VOLUME_DATA_GROUPNAME].arrays():
        arr_view = arr[...]
        # if QUANTIZATION_DATA_DICT_ATTR_NAME in arr.attrs:
        #     data_dict = arr.attrs[QUANTIZATION_DATA_DICT_ATTR_NAME]
        #     data_dict['data'] = arr_view
        #     arr_view = decode_quantized_data(data_dict)
        #     if isinstance(arr_view, da.Array):
        #         arr_view = arr_view.compute()

        mean_val = float(str(np.mean(arr_view)))
        std_val = float(str(np.std(arr_view)))
        max_val = float(str(arr_view.max()))
        min_val = float(str(arr_view.min()))
        grid_dimensions_val: tuple[int, int, int] = arr.shape

        mean_dict[str(arr_name)] = mean_val
        std_dict[str(arr_name)] = std_val
        max_dict[str(arr_name)] = max_val
        min_dict[str(arr_name)] = min_val
        grid_dimensions_dict[str(arr_name)] = grid_dimensions_val

    lattice_dict = {}
    lattice_ids = []
    
    if SEGMENTATION_DATA_GROUPNAME in root:
        for gr_name, gr in root[SEGMENTATION_DATA_GROUPNAME].groups():
            # each key is lattice id
            lattice_id = int(gr_name)

            segm_downsamplings = sorted(gr.group_keys())
            # convert to ints
            segm_downsamplings = sorted([int(x) for x in segm_downsamplings])

            lattice_dict[lattice_id] = segm_downsamplings
            lattice_ids.append(lattice_id)
                        
    # Sampled grid dimensions: in zattrs, they have 0,1,2 downsampling levels (XY is cut x2, Z stays)
    # We have 1, 2, 4 (according to downsampling factor)
    # I do 0,1,2
    voxel_sizes_in_downsamplings = _compose_voxel_sizes_in_downsamplings_dict(ome_zarr_root=ome_zarr_root)

    # origin is probably (0, 0, 0), as there is no 'translation' in zattrs
    # Ctrl+F 'origin' https://ngff.openmicroscopy.org/latest/#multiscale-md
    origin = (0, 0, 0)

    return {
        'general': {
            'source_db_name': source_db_name,
            'source_db_id': source_db_id,
        },
        'volumes': {
            'volume_downsamplings': volume_downsamplings,
            # downsamplings have different voxel size so it is a dict
            'voxel_size': voxel_sizes_in_downsamplings,
            'origin': origin,
            'grid_dimensions': grid_dimensions_dict['0'],
            'sampled_grid_dimensions': grid_dimensions_dict,
            'mean': mean_dict,
            'std': std_dict,
            'max': max_dict,
            'min': min_dict,
            'volume_force_dtype': volume_force_dtype.str
        },
        'segmentation_lattices': {
            'segmentation_lattice_ids': lattice_ids,
            'segmentation_downsamplings': lattice_dict
        },
        'segmentation_meshes': {
            'mesh_component_numbers': {},
            'detail_lvl_to_fraction': {}
        }
    }

# NOTE: To be clarified how to get actual annotations:
# https://github.com/ome/ngff/issues/163#issuecomment-1328009660
# This one just uses label-value originated from .zattrs and copied to set_table of 0th resolution
def extract_ome_zarr_annotations(our_zarr_structure, ome_zarr_root):
    dapi_channel_color_hex = ome_zarr_root.attrs['omero']['channels'][1]['color']
    dapi_channel_color_rgba = ImageColor.getcolor(f'#{dapi_channel_color_hex}', "RGBA")
    dapi_channel_color_rgba_fractional = [i/255 for i in dapi_channel_color_rgba]
    d = {
        "segment_list": []
    }
    segment_list = d['segment_list']
    set_table = our_zarr_structure[SEGMENTATION_DATA_GROUPNAME][0][0].set_table[...][0]
    for label_value in set_table.keys():
        if label_value != '0':
            segment_list.append(
                {
                    "id": int(label_value),
                    "parent_id": 0,
                    "biological_annotation": {
                        "name": f"segment {label_value}",
                        "description": None,
                        "number_of_instances": 1,
                        "external_references": [
                        ]
                    },
                    "colour": dapi_channel_color_rgba_fractional,
                    "mesh_list": [],
                    "three_d_volume": {
                        "lattice_id": 0,
                        "value": float(label_value),
                        "transform_id": None
                    },
                    "shape_primitive_list": []
                }
            )

    return d


# returns zarr structure to be stored with db.store
# NOTE: just one channel
def process_ome_zarr(ome_zarr_path, temp_zarr_hierarchy_storage_path, source_db_id, source_db_name):
    ome_zarr_root = zarr.open_group(ome_zarr_path)
    
    entry_id = source_db_name + '-' + source_db_id
    our_zarr_structure_path = temp_zarr_hierarchy_storage_path / entry_id
    our_zarr_structure = zarr.open_group(temp_zarr_hierarchy_storage_path / entry_id, mode='w')

    # PROCESSING VOLUME
    # NOTE: just Dapi channel (second in sample_ome_zarr_from_ome_zarr_py_docs/6001240.zarr/.zattrs)
    volume_data_gr = our_zarr_structure.create_group(VOLUME_DATA_GROUPNAME)
    for volume_arr_resolution, volume_arr in ome_zarr_root.arrays():
        # hardcoded only second channel
        # TODO: ask if swapaxes is correct
        corrected_volume_arr_data = volume_arr[...][1].swapaxes(0,2)
        our_volume_resolution_arr = volume_data_gr.create_dataset(
            name=volume_arr_resolution,
            shape=corrected_volume_arr_data.shape,
            data=corrected_volume_arr_data
        )

    

    
    # PROCESSING SEGMENTATION
    segmentation_data_gr = our_zarr_structure.create_group(SEGMENTATION_DATA_GROUPNAME)
    lattice_id_gr = segmentation_data_gr.create_group('0')

    # hardcoded labels [0], should iterate over them, but for sample file ok (just 0 label is here)
    # arr_name is resolution
    for arr_name, arr in ome_zarr_root.labels[0].arrays():
        # swapaxes (ZYX to XYZ), and no channel dimension (there is just single channel dimension)
        corrected_arr_data = arr[...][0].swapaxes(0,2)
        our_resolution_gr = lattice_id_gr.create_group(arr_name)
        our_arr = our_resolution_gr.create_dataset(
            name='grid',
            shape=corrected_arr_data.shape,
            data=corrected_arr_data
        )
        
        our_set_table = our_resolution_gr.create_dataset(
            name='set_table',
            dtype=object,
            object_codec=numcodecs.JSON(),
            shape=1
        )
        
        d = {}
        for value in np.unique(our_arr[...]):
            d[str(value)] = [int(value)]

        our_set_table[...] = [d]

    # NOTE: single volume_force_dtype 
    grid_metadata = extract_ome_zarr_metadata(
        our_zarr_structure=our_zarr_structure,
        volume_force_dtype=volume_data_gr[0].dtype,
        source_db_id=source_db_id,
        source_db_name=source_db_name,
        ome_zarr_root=ome_zarr_root
    )

    annotation_metadata = extract_ome_zarr_annotations(
        our_zarr_structure=our_zarr_structure,
        ome_zarr_root=ome_zarr_root
    )

    SFFPreprocessor.temp_save_metadata(grid_metadata, GRID_METADATA_FILENAME, our_zarr_structure_path)
    SFFPreprocessor.temp_save_metadata(annotation_metadata, ANNOTATION_METADATA_FILENAME, our_zarr_structure_path)

    # need 3D dataset
    return our_zarr_structure

async def store_ome_zarr_structure(db_path, temp_ome_zarr_structure, source_db, entry_id):
    new_db_path = Path(db_path)
    if new_db_path.is_dir() == False:
        new_db_path.mkdir()

    db = FileSystemVolumeServerDB(new_db_path, store_type='zip')
    await db.store(namespace=source_db, key=entry_id, temp_store_path=Path(temp_ome_zarr_structure.store.path))

async def main():
    args = parse_script_args()
    

    if args.raw_input_files_dir_path:
        raw_input_files_dir_path = args.raw_input_files_dir_path
    else:
        raise ValueError('No raw input files dir path is provided as argument')
    
    if args.temp_zarr_hierarchy_storage_path:
        temp_zarr_hierarchy_storage_path = args.temp_zarr_hierarchy_storage_path
    else:
        # raise ValueError('No temp_zarr_hierarchy_storage_path is provided as argument')
        temp_zarr_hierarchy_storage_path = TEMP_ZARR_HIERARCHY_STORAGE_PATH / args.db_path.name
        
    # NOTE: not maintained currently (outdated arg numbers etc.)
    if args.create_parametrized_dbs:
        # TODO: add quantize and raw input files dir path here too
        remove_files_or_folders_by_pattern('db_*/')
        storing_params_dict = create_dict_of_input_params_for_storing(
            chunking_mode=CHUNKING_MODES,
            compressors=COMPRESSORS
        )
        write_dict_to_txt(storing_params_dict, PARAMETRIZED_DBS_INPUT_PARAMS_FILEPATH)
        for db_id, param_set in storing_params_dict.items():
            await create_db(Path(f'db_{db_id}'), params_for_storing=param_set,
                temp_zarr_hierarchy_storage_path=temp_zarr_hierarchy_storage_path)
    elif args.db_path:
        # print(args.quantize_volume_data_dtype_str)
        params_for_storing={
            'chunking_mode': 'auto',
            'compressor': Blosc(cname='lz4', clevel=5, shuffle=Blosc.SHUFFLE, blocksize=0),
            'store_type': 'zip'
        }
        if args.quantize_volume_data_dtype_str:
            params_for_storing['quantize_dtype_str'] = args.quantize_volume_data_dtype_str

        if args.single_entry:
            if args.entry_id and args.source_db and args.source_db_id and args.source_db_name:
                if args.ome_zarr_path:
                    # do ome zarr thing
                    zarr_structure_to_be_saved = process_ome_zarr(
                        ome_zarr_path=args.ome_zarr_path,
                        temp_zarr_hierarchy_storage_path=temp_zarr_hierarchy_storage_path,
                        source_db_id=args.source_db_id,
                        source_db_name=args.source_db_name)
                    await store_ome_zarr_structure(args.db_path, zarr_structure_to_be_saved, args.source_db, args.entry_id)
                    print(1)
                else:
                    single_entry_folder_path = args.single_entry
                    single_entry_id = args.entry_id
                    single_entry_source_db = args.source_db

                    if args.force_volume_dtype:
                        force_volume_dtype = args.force_volume_dtype
                    else:
                        force_volume_dtype = None

                    await add_entry_to_db(
                        Path(args.db_path),
                        params_for_storing=params_for_storing,
                        input_files_dir=single_entry_folder_path,
                        entry_id=single_entry_id,
                        source_db=single_entry_source_db,
                        force_volume_dtype=force_volume_dtype,
                        temp_zarr_hierarchy_storage_path=temp_zarr_hierarchy_storage_path,
                        source_db_id=args.source_db_id,
                        source_db_name=args.source_db_name
                        )
            else:
                raise ValueError('args.entry_id and args.source_db and args.source_db_id and args.source_db_name are required for single entry mode')
        else:
            await create_db(Path(args.db_path),
                params_for_storing=params_for_storing,
                raw_input_files_dir_path=raw_input_files_dir_path,
                temp_zarr_hierarchy_storage_path=temp_zarr_hierarchy_storage_path)
    else:
        raise ValueError('No db path is provided as argument')

def parse_script_args():
    parser=argparse.ArgumentParser()
    parser.add_argument("--db_path", type=Path, default=DEFAULT_DB_PATH, help='path to db folder')
    parser.add_argument("--raw_input_files_dir_path", type=Path, default=RAW_INPUT_FILES_DIR, help='path to directory with input files (maps and sff)')
    parser.add_argument("--create_parametrized_dbs", action='store_true')
    parser.add_argument("--quantize_volume_data_dtype_str", action="store", choices=['u1', 'u2'])
    parser.add_argument('--single_entry', type=Path, help='path to folder with MAP and segmentation files')
    parser.add_argument('--entry_id', type=str, help='entry id to be used as DB folder name')
    parser.add_argument('--source_db', type=str, help='source database name to be used as DB folder name')
    parser.add_argument('--force_volume_dtype', type=str, help='dtype of volume data to be used')
    parser.add_argument("--temp_zarr_hierarchy_storage_path", type=Path, help='path to db working directory')
    parser.add_argument('--source_db_id', type=str, help='actual source db id for metadata')
    parser.add_argument('--source_db_name', type=str, help='actual source db name for metadata')
    parser.add_argument('--ome_zarr_path', type=Path)
    args=parser.parse_args()
    return args

if __name__ == '__main__':
    asyncio.run(main())


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
