import os
from argparse import ArgumentError
import logging
import shutil
from typing import Dict, Tuple, Union
from pathlib import Path
import json
import zarr
from sys import stdout
import numpy as np
import dask.array as da
from timeit import default_timer as timer
import tensorstore as ts

from preprocessor.src.preprocessors.implementations.sff.preprocessor.constants import DB_NAMESPACES, \
    QUANTIZATION_DATA_DICT_ATTR_NAME, SEGMENTATION_DATA_GROUPNAME, \
    VOLUME_DATA_GROUPNAME, ZIP_STORE_DATA_ZIP_NAME
from preprocessor.src.preprocessors.implementations.sff.preprocessor.sff_preprocessor import \
    ANNOTATION_METADATA_FILENAME, GRID_METADATA_FILENAME
from preprocessor.src.preprocessors.implementations.sff.preprocessor.sff_preprocessor import \
    open_zarr_structure_from_path
from preprocessor.src.tools.quantize_data.quantize_data import decode_quantized_data

from .local_disk_preprocessed_medata import LocalDiskPreprocessedMetadata
from db.interface.i_preprocessed_db import IPreprocessedDb, ProcessedOnlyVolumeSliceData, ProcessedVolumeSliceData
from ...interface.i_preprocessed_medatada import IPreprocessedMetadata


class ReadContext():
    async def read(self, lattice_id: int, down_sampling_ratio: int) -> Dict:
        '''
        Deprecated.
        Reads specific (down)sampling of segmentation data from specific entry from DB
        based on key (e.g. EMD-1111), lattice_id (e.g. 0), and downsampling ratio
        (1 => original data, 2 => downsampled by factor of 2 etc.)
        '''
        print('This method is deprecated, please use read_slice method instead')
        try:
            root: zarr.hierarchy.group = zarr.group(self.store)

            segm_arr = None
            segm_dict = None
            if SEGMENTATION_DATA_GROUPNAME in root:
                segm_arr = root[SEGMENTATION_DATA_GROUPNAME][lattice_id][down_sampling_ratio].grid
                segm_dict = root[SEGMENTATION_DATA_GROUPNAME][lattice_id][down_sampling_ratio].set_table[0]
            volume_arr: zarr.core.Array = root[VOLUME_DATA_GROUPNAME][down_sampling_ratio]

            if segm_arr:
                d = {
                    "segmentation_arr": {
                        "category_set_ids": segm_arr,
                        "category_set_dict": segm_dict
                    },
                    "volume_arr": volume_arr
                }
            else:
                d = {
                    "segmentation_arr": {
                        "category_set_ids": None,
                        "category_set_dict": None
                    },
                    "volume_arr": volume_arr
                }

        except Exception as e:
            logging.error(e, stack_info=True, exc_info=True)
            raise e

        return d

    async def read_slice(self, down_sampling_ratio: int,
                         box: Tuple[Tuple[int, int, int], Tuple[int, int, int]], mode: str = 'dask',
                         timer_printout=False, lattice_id: int = 0) -> ProcessedVolumeSliceData:
        '''
        Reads a slice from a specific (down)sampling of segmentation and volume data
        from specific entry from DB based on key (e.g. EMD-1111), lattice_id (e.g. 0),
        downsampling ratio (1 => original data, 2 => downsampled by factor of 2 etc.),
        and slice box (vec3, vec3) 
        '''
        try:

            box = normalize_box(box)

            root: zarr.hierarchy.group = zarr.group(self.store)

            segm_arr = None
            segm_dict = None
            if SEGMENTATION_DATA_GROUPNAME in root and (lattice_id is not None):
                segm_arr = root[SEGMENTATION_DATA_GROUPNAME][lattice_id][down_sampling_ratio].grid
                assert (np.array(box[1]) <= np.array(segm_arr.shape)).all(), \
                    f'requested box {box} does not correspond to arr dimensions'
                segm_dict = root[SEGMENTATION_DATA_GROUPNAME][lattice_id][down_sampling_ratio].set_table[0]
            volume_arr: zarr.core.Array = root[VOLUME_DATA_GROUPNAME][down_sampling_ratio]

            assert (np.array(box[0]) >= np.array([0, 0, 0])).all(), \
                f'requested box {box} does not correspond to arr dimensions'
            assert (np.array(box[1]) <= np.array(volume_arr.shape)).all(), \
                f'requested box {box} does not correspond to arr dimensions'

            segm_slice: np.ndarray
            volume_slice: np.ndarray
            start = timer()
            if mode == 'zarr_colon':
                # 2: zarr slicing via : notation
                if segm_arr: segm_slice = self.__get_slice_from_zarr_three_d_arr(arr=segm_arr, box=box)
                volume_slice = self.__get_slice_from_zarr_three_d_arr(arr=volume_arr, box=box)
            elif mode == 'zarr_gbs':
                # 3: zarr slicing via get_basic_selection and python slices
                if segm_arr: segm_slice = self.__get_slice_from_zarr_three_d_arr_gbs(arr=segm_arr, box=box)
                volume_slice = self.__get_slice_from_zarr_three_d_arr_gbs(arr=volume_arr, box=box)
            elif mode == 'dask':
                # 4: dask slicing: https://github.com/zarr-developers/zarr-python/issues/478#issuecomment-531148674
                if segm_arr: segm_slice = self.__get_slice_from_zarr_three_d_arr_dask(arr=segm_arr, box=box)
                volume_slice = self.__get_slice_from_zarr_three_d_arr_dask(arr=volume_arr, box=box)
            elif mode == 'dask_from_zarr':
                if segm_arr: segm_slice = self.__get_slice_from_zarr_three_d_arr_dask_from_zarr(arr=segm_arr, box=box)
                volume_slice = self.__get_slice_from_zarr_three_d_arr_dask_from_zarr(arr=volume_arr, box=box)
            elif mode == 'tensorstore':
                # TODO: figure out variable types https://stackoverflow.com/questions/64924224/getting-a-view-of-a-zarr-array-slice
                # it can be 'view' or np array etc.
                if segm_arr: segm_slice = self.__get_slice_from_zarr_three_d_arr_tensorstore(arr=segm_arr, box=box)
                volume_slice = self.__get_slice_from_zarr_three_d_arr_tensorstore(arr=volume_arr, box=box)

            end = timer()

            # check if volume_arr was originally quantized data (e.g. some attr on array, e.g. data_dict attr with data_dict)
            # if yes, decode volume_slice (reassamble data dict from data_dict attr, just add 'data' key with volume_slice)
            # do .compute on output of decode_quantized_data function if output is da.Array

            if QUANTIZATION_DATA_DICT_ATTR_NAME in volume_arr.attrs:
                data_dict = volume_arr.attrs[QUANTIZATION_DATA_DICT_ATTR_NAME]
                data_dict['data'] = volume_slice
                volume_slice = decode_quantized_data(data_dict)
                if isinstance(volume_slice, da.Array):
                    volume_slice = volume_slice.compute()

            if timer_printout == True:
                print(f'read_slice with mode {mode}: {end - start}')
            if segm_arr:
                d = {
                    "segmentation_slice": {
                        "category_set_ids": segm_slice,
                        "category_set_dict": segm_dict
                    },
                    "volume_slice": volume_slice
                }
            else:
                d = {
                    "segmentation_slice": {
                        "category_set_ids": None,
                        "category_set_dict": None
                    },
                    "volume_slice": volume_slice
                }
        except Exception as e:
            logging.error(e, stack_info=True, exc_info=True)
            raise e

        return d

    async def read_meshes(self, segment_id: int, detail_lvl: int) -> list[object]:
        '''
        Returns list of meshes for a given segment, entry, detail lvl
        '''
        try:
            mesh_list = []
            root: zarr.hierarchy.group = zarr.group(self.store)
            mesh_list_group = root[SEGMENTATION_DATA_GROUPNAME][segment_id][detail_lvl]
            for mesh_name, mesh in mesh_list_group.groups():
                mesh_data = {
                    'mesh_id': int(mesh_name)
                }
                for mesh_component_name, mesh_component_arr in mesh.arrays():
                    mesh_data[f'{mesh_component_name}'] = mesh_component_arr[...]
                mesh_list.append(mesh_data)
        except Exception as e:
            logging.error(e, stack_info=True, exc_info=True)
            raise e

        return mesh_list

    async def read_volume_slice(self, down_sampling_ratio: int,
                         box: Tuple[Tuple[int, int, int], Tuple[int, int, int]], mode: str = 'dask',
                         timer_printout=False) -> ProcessedOnlyVolumeSliceData:
        try:

            box = normalize_box(box)

            root: zarr.hierarchy.group = zarr.group(self.store)

            volume_arr: zarr.core.Array = root[VOLUME_DATA_GROUPNAME][down_sampling_ratio]

            assert (np.array(box[0]) >= np.array([0, 0, 0])).all(), \
                f'requested box {box} does not correspond to arr dimensions'
            assert (np.array(box[1]) <= np.array(volume_arr.shape)).all(), \
                f'requested box {box} does not correspond to arr dimensions'

            volume_slice: np.ndarray
            start = timer()
            if mode == 'zarr_colon':
                # 2: zarr slicing via : notation
                volume_slice = self.__get_slice_from_zarr_three_d_arr(arr=volume_arr, box=box)
            elif mode == 'zarr_gbs':
                # 3: zarr slicing via get_basic_selection and python slices
                volume_slice = self.__get_slice_from_zarr_three_d_arr_gbs(arr=volume_arr, box=box)
            elif mode == 'dask':
                # 4: dask slicing: https://github.com/zarr-developers/zarr-python/issues/478#issuecomment-531148674
                volume_slice = self.__get_slice_from_zarr_three_d_arr_dask(arr=volume_arr, box=box)
            elif mode == 'dask_from_zarr':
                volume_slice = self.__get_slice_from_zarr_three_d_arr_dask_from_zarr(arr=volume_arr, box=box)
            elif mode == 'tensorstore':
                volume_slice = self.__get_slice_from_zarr_three_d_arr_tensorstore(arr=volume_arr, box=box)

            end = timer()

            # check if volume_arr was originally quantized data (e.g. some attr on array, e.g. data_dict attr with data_dict)
            # if yes, decode volume_slice (reassamble data dict from data_dict attr, just add 'data' key with volume_slice)
            # do .compute on output of decode_quantized_data function if output is da.Array

            if QUANTIZATION_DATA_DICT_ATTR_NAME in volume_arr.attrs:
                data_dict = volume_arr.attrs[QUANTIZATION_DATA_DICT_ATTR_NAME]
                data_dict['data'] = volume_slice
                volume_slice = decode_quantized_data(data_dict)
                if isinstance(volume_slice, da.Array):
                    volume_slice = volume_slice.compute()

            if timer_printout == True:
                print(f'read_slice with mode {mode}: {end - start}')

            d = {
                "volume_slice": volume_slice
                }

        except Exception as e:
            logging.error(e, stack_info=True, exc_info=True)
            raise e

        return d

    def __get_slice_from_zarr_three_d_arr(self, arr: zarr.core.Array,
                                          box: Tuple[Tuple[int, int, int], Tuple[int, int, int]]):
        '''
        Based on (vec3, vec3) tuple (coordinates of corners of the box)
        returns a slice of 3d array
        '''
        sliced = arr[
                 box[0][0]: box[1][0] + 1,
                 box[0][1]: box[1][1] + 1,
                 box[0][2]: box[1][2] + 1
                 ]
        return sliced

    def __get_slice_from_zarr_three_d_arr_gbs(self, arr: zarr.core.Array,
                                              box: Tuple[Tuple[int, int, int], Tuple[int, int, int]]):
        # TODO: check if slice is correct and equal to : notation slice
        sliced = arr.get_basic_selection(
            (
                slice(box[0][0], box[1][0] + 1),
                slice(box[0][1], box[1][1] + 1),
                slice(box[0][2], box[1][2] + 1)
            )
        )
        return sliced

    def __get_slice_from_zarr_three_d_arr_dask(self, arr: zarr.core.Array,
                                               box: Tuple[Tuple[int, int, int], Tuple[int, int, int]]):
        # TODO: check if slice is correct and equal to : notation slice
        # 4: dask slicing: https://github.com/zarr-developers/zarr-python/issues/478#issuecomment-531148674
        zd = da.from_array(arr, chunks=arr.chunks)
        sliced = zd[
                 box[0][0]: box[1][0] + 1,
                 box[0][1]: box[1][1] + 1,
                 box[0][2]: box[1][2] + 1
                 ]
        return sliced.compute()

    def __get_slice_from_zarr_three_d_arr_dask_from_zarr(self, arr: zarr.core.Array,
                                                         box: Tuple[Tuple[int, int, int], Tuple[int, int, int]]):
        zd = da.from_zarr(arr, chunks=arr.chunks)
        sliced = zd[
                 box[0][0]: box[1][0] + 1,
                 box[0][1]: box[1][1] + 1,
                 box[0][2]: box[1][2] + 1
                 ]
        return sliced.compute()

    def __get_slice_from_zarr_three_d_arr_tensorstore(self, arr: zarr.core.Array,
                                                      box: Tuple[Tuple[int, int, int], Tuple[int, int, int]]):
        # TODO: check if slice is correct and equal to : notation slice
        # TODO: await? # store - future object, result - ONE of the ways how to get it sync (can be async)
        # store.read() - returns everything as future object. again result() or other methods
        # can be store[1:10].read() ...
        print('This method is MAY not work properly for ZIP store. Needs to be checked')
        path = self.__get_path_to_zarr_object(arr)
        store = ts.open(
            {
                'driver': 'zarr',
                'kvstore': {
                    'driver': 'file',
                    'path': str(path.resolve()),
                },
            },
            read=True
        ).result()
        sliced = store[
                 box[0][0]: box[1][0] + 1,
                 box[0][1]: box[1][1] + 1,
                 box[0][2]: box[1][2] + 1
                 ].read().result()
        return sliced

    def __get_path_to_zarr_object(self, zarr_obj: Union[zarr.hierarchy.Group, zarr.core.Array]) -> Path:
        '''
        Returns Path to zarr object (array or group)
        '''
        path: Path = Path(zarr_obj.store.path).resolve() / zarr_obj.path
        return path

    def close(self):
        if hasattr(self.store, 'close'):
            self.store.close()
        else:
            pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if hasattr(self.store, 'close'):
            self.store.close()
        else:
            pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args, **kwargs):
        if hasattr(self.store, 'aclose'):
            await self.store.aclose()
        if hasattr(self.store, 'close'):
            self.store.close()
        else:
            pass

    def __init__(self, db: IPreprocessedDb, namespace: str, key: str):
        self.db = db
        self.path = db.path_to_zarr_root_data(namespace=namespace, key=key)
        assert self.path.exists(), f'Path {self.path} does not exist'
        self.key = key
        self.namespace = namespace
        if self.db.store_type == 'directory':
            self.store = zarr.DirectoryStore(path=self.path)
        elif self.db.store_type == 'zip':
            self.store = zarr.ZipStore(
                path=self.path,
                compression=0,
                allowZip64=True,
                mode='r'
            )


class LocalDiskPreprocessedDb(IPreprocessedDb):
    async def list_sources(self) -> list[str]:
        sources: list[str] = []
        for file in os.listdir(self.folder):
            d = os.path.join(self.folder, file)
            if os.path.isdir(d):
                if file == "interface" or file == "implementations" or file.startswith("_"):
                    continue

                sources.append(str(file))

        return sources

    async def list_entries(self, source: str, limit: int) -> list[str]:
        entries: list[str] = []
        source_path = os.path.join(self.folder, source)
        for file in os.listdir(source_path):
            entries.append(file)
            limit -= 1
            if limit == 0:
                break

        return entries

    def __init__(self, folder: Path, store_type: str = 'zip'):
        # either create of say it doesn't exist
        if not folder.is_dir():
            raise ValueError(f"Input folder doesn't exist {folder}")

        self.folder = folder

        if not store_type in ['directory', 'zip']:
            raise ArgumentError(f'store type is not supported: {store_type}')

        self.store_type = store_type

    def _path_to_object(self, namespace: str, key: str) -> Path:
        '''
        Returns path to DB entry based on namespace and key
        '''
        return self.folder / namespace / key

    def path_to_zarr_root_data(self, namespace: str, key: str) -> Path:
        '''
        Returns path to actual zarr structure root depending on store type
        '''
        if self.store_type == 'directory':
            return self._path_to_object(namespace=namespace, key=key)
        elif self.store_type == 'zip':
            return self._path_to_object(namespace=namespace, key=key) / ZIP_STORE_DATA_ZIP_NAME
        else:
            raise ValueError(f'store type is not supported: {self.store_type}')

    async def contains(self, namespace: str, key: str) -> bool:
        '''
        Checks if DB entry exists
        '''
        return self._path_to_object(namespace, key).is_dir()
    
    async def delete(self, namespace: str, key: str):
        '''
        Removes entry
        '''
        path = self._path_to_object(namespace=namespace, key=key)
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        else:
            raise Exception(f'Entry path {path} does not exists or is not a dir')

    def remove_all_entries(self):
        '''
        Removes all entries from db
        used before another run of building db to build it from scratch without interfering with
        previously existing entries
        '''
        for namespace in DB_NAMESPACES:
            content = sorted((self.folder / namespace).glob('*'))
            for path in content:
                if path.is_file():
                    path.unlink()
                if path.is_dir():
                    shutil.rmtree(path, ignore_errors=True)

    async def store(self, namespace: str, key: str, temp_store_path: Path) -> bool:
        '''
        Takes path to temp zarr structure returned by preprocessor as argument 
        '''
        # Storing as a file (ZIP, bzip2 compression)
        # Compression constants for compression arg of ZipStore()
        # ZIP_STORED = 0
        # ZIP_DEFLATED = 8 (zlib)
        # ZIP_BZIP2 = 12
        # ZIP_LZMA = 1
        # close store after writing, or use 'with' https://zarr.readthedocs.io/en/stable/api/storage.html#zarr.storage.ZipStore
        temp_store: zarr.storage.DirectoryStore = zarr.DirectoryStore(str(temp_store_path))

        # WHAT NEEDS TO BE CHANGED
        # perm_store = zarr.ZipStore(self._path_to_object(namespace, key) + '.zip', mode='w', compression=12)

        if self.store_type == 'directory':
            perm_store = zarr.DirectoryStore(str(self._path_to_object(namespace, key)))
            zarr.copy_store(temp_store, perm_store, log=stdout)
        elif self.store_type == 'zip':
            entry_dir_path = self._path_to_object(namespace, key)
            entry_dir_path.mkdir(parents=True, exist_ok=True)
            perm_store = zarr.ZipStore(
                path=str(self.path_to_zarr_root_data(namespace, key)),
                compression=0,
                allowZip64=True,
                mode='w'
            )
            zarr.copy_store(temp_store, perm_store, log=stdout)
        else:
            raise ArgumentError('store type is wrong: {self.store_type}')

        # PART BELOW WILL STAY AS IT IS probably
        print("A: " + str(temp_store_path))
        print("B: " + GRID_METADATA_FILENAME)

        shutil.copy2(temp_store_path / GRID_METADATA_FILENAME,
                     self._path_to_object(namespace, key) / GRID_METADATA_FILENAME)
        if (temp_store_path / ANNOTATION_METADATA_FILENAME).exists():
            shutil.copy2(temp_store_path / ANNOTATION_METADATA_FILENAME,
                         self._path_to_object(namespace, key) / ANNOTATION_METADATA_FILENAME)
        else:
            print('no annotation metadata file found, continuing without copying it')

        if self.store_type == 'zip':
            perm_store.close()

        temp_store.rmdir()
        # TODO: check if copied and store closed properly
        return True

    def read(self, namespace: str, key: str) -> ReadContext:
        return ReadContext(db=self, namespace=namespace, key=key)

    async def read_metadata(self, namespace: str, key: str) -> IPreprocessedMetadata:
        path: Path = self._path_to_object(namespace=namespace, key=key) / GRID_METADATA_FILENAME
        with open(path.resolve(), 'r', encoding='utf-8') as f:
            # reads into dict
            read_json_of_metadata: Dict = json.load(f)
        return LocalDiskPreprocessedMetadata(read_json_of_metadata)

    async def read_annotations(self, namespace: str, key: str) -> Dict:
        path: Path = self._path_to_object(namespace=namespace, key=key) / ANNOTATION_METADATA_FILENAME
        with open(path.resolve(), 'r', encoding='utf-8') as f:
            # reads into dict
            read_json_of_metadata: Dict = json.load(f)
        return read_json_of_metadata


def normalize_box(box: Tuple[Tuple[int, int, int], Tuple[int, int, int]]) -> Tuple[
    Tuple[int, int, int], Tuple[int, int, int]]:
    '''Normalizes box so that first point is less than 2nd with respect to X, Y, Z'''
    p1 = box[0]
    p2 = box[1]

    new_p1 = tuple(np.minimum(p1, p2))
    new_p2 = tuple(np.maximum(p1, p2))

    return (
        new_p1,
        new_p2
    )
