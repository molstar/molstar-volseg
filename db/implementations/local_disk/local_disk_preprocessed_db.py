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

from preprocessor.src.preprocessors.implementations.sff.preprocessor.sff_preprocessor import ANNOTATION_METADATA_FILENAME, GRID_METADATA_FILENAME, SEGMENTATION_DATA_GROUPNAME, VOLUME_DATA_GROUPNAME
from preprocessor.src.preprocessors.implementations.sff.preprocessor.sff_preprocessor import open_zarr_structure_from_path

from .local_disk_preprocessed_medata import LocalDiskPreprocessedMetadata
from db.interface.i_preprocessed_db import IPreprocessedDb, ProcessedVolumeSliceData
from ...interface.i_preprocessed_medatada import IPreprocessedMetadata


class LocalDiskPreprocessedDb(IPreprocessedDb):
    @staticmethod
    def __path_to_object__(namespace: str, key: str) -> Path:
        '''
        Returns path to DB entry based on namespace and key
        '''
        return Path(__file__).resolve().parents[2] / namespace / key

    async def contains(self, namespace: str, key: str) -> bool:
        '''
        Checks if DB entry exists
        '''
        return self.__path_to_object__(namespace, key).is_dir()
    
    def remove_all_entries(self, namespace: str = 'emdb'):
        '''
        Removes all entries from dir of certain source db (namespace);
        used before another run of building db to build it from scratch without interfering with
        previously existing entries
        '''
        content = sorted((Path(__file__).resolve().parents[2] / namespace).glob('*'))
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
        # perm_store = zarr.ZipStore(self.__path_to_object__(namespace, key) + '.zip', mode='w', compression=12)
        perm_store = zarr.DirectoryStore(str(self.__path_to_object__(namespace, key)))
        zarr.copy_store(temp_store, perm_store, log=stdout)

        # TODO: shutil should work with Path objects, but just in case
        shutil.copy2(temp_store_path / GRID_METADATA_FILENAME, self.__path_to_object__(namespace, key) / GRID_METADATA_FILENAME)
        if (temp_store_path / ANNOTATION_METADATA_FILENAME).exists():
            shutil.copy2(temp_store_path / ANNOTATION_METADATA_FILENAME, self.__path_to_object__(namespace, key) / ANNOTATION_METADATA_FILENAME)
        else:
            print('no annotation metadata file found, continuing without copying it')
        # TODO: check if temp dir will be correctly removed and read at the beginning, given that there is a JSON file inside
        # temp_store.close()
        # perm_store.close()
        temp_store.rmdir()
        # TODO: check if copied and store closed properly
        return True

    # TODO: evaluate passing a dict instead of 4 params
    async def read(self, namespace: str, key: str, lattice_id: int, down_sampling_ratio: int) -> Dict:
        '''
        Deprecated.
        Reads specific (down)sampling of segmentation data from specific entry from DB
        based on key (e.g. EMD-1111), lattice_id (e.g. 0), and downsampling ratio
        (1 => original data, 2 => downsampled by factor of 2 etc.)
        '''
        print('This method is deprecated, please use read_slice method instead')
        path: Path = self.__path_to_object__(namespace=namespace, key=key)
        store: zarr.storage.DirectoryStore = zarr.DirectoryStore(str(path))
        # Re-create zarr hierarchy from opened store
        root: zarr.hierarchy.group = zarr.group(store=store)
        
        read_segm_arr: np.ndarray = root[SEGMENTATION_DATA_GROUPNAME][lattice_id]
        read_volume_arr: np.ndarray = root[VOLUME_DATA_GROUPNAME]
        # both volume and segm data
        return {
            'segmentation': read_segm_arr,
            'volume': read_volume_arr
        }

    async def read_slice(self, namespace: str, key: str, lattice_id: int, down_sampling_ratio: int, box: Tuple[Tuple[int, int, int], Tuple[int, int, int]], mode: str = 'dask') -> ProcessedVolumeSliceData:
        '''
        Reads a slice from a specific (down)sampling of segmentation and volume data
        from specific entry from DB based on key (e.g. EMD-1111), lattice_id (e.g. 0),
        downsampling ratio (1 => original data, 2 => downsampled by factor of 2 etc.),
        and slice box (vec3, vec3) 
        '''
        path: Path = self.__path_to_object__(namespace=namespace, key=key)
        root: zarr.hierarchy.group = open_zarr_structure_from_path(path)
        # TODO: segm arr will change address as there going to be a group for each ratio instead of zarr arr
        # TODO: in that group there should be arr of "values" and dict object
        segm_arr = None
        segm_dict = None
        if SEGMENTATION_DATA_GROUPNAME in root:
            segm_arr = root[SEGMENTATION_DATA_GROUPNAME][lattice_id][down_sampling_ratio].grid
            segm_dict = root[SEGMENTATION_DATA_GROUPNAME][lattice_id][down_sampling_ratio].set_table[0]
        volume_arr: zarr.core.Array = root[VOLUME_DATA_GROUPNAME][down_sampling_ratio]
        
        # TODO: segm slice would be TypedDict (arr + dict with sets)
        segm_slice: np.ndarray
        volume_slice: np.ndarray
        start = timer()
        if mode == 'zarr_colon':
            # 2: zarr slicing via : notation
            # TODO: here and in each mode: change impl of segm slice: get_slice from segm_arr separately
            # and then get the corresponding dict (json obj from that group) which explain the meaning of "values" in segm_arr (pointers to sets in dict)
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
        return d

    async def read_grid_metadata(self, namespace: str, key: str) -> IPreprocessedMetadata:
        path: Path = self.__path_to_object__(namespace=namespace, key=key) / GRID_METADATA_FILENAME
        with open(path.resolve(), 'r', encoding='utf-8') as f:
            # reads into dict
            read_json_of_metadata: Dict = json.load(f)
        return LocalDiskPreprocessedMetadata(read_json_of_metadata)
    
    async def read_annotation_metadata(self, namespace: str, key: str) -> Dict:
        path: Path = self.__path_to_object__(namespace=namespace, key=key) / ANNOTATION_METADATA_FILENAME
        with open(path.resolve(), 'r', encoding='utf-8') as f:
            # reads into dict
            read_json_of_metadata: Dict = json.load(f)
        return read_json_of_metadata

    def __get_slice_from_zarr_three_d_arr(self, arr: zarr.core.Array, box: Tuple[Tuple[int, int, int], Tuple[int, int, int]]):
        '''
        Based on (vec3, vec3) tuple (coordinates of corners of the box)
        returns a slice of 3d array
        '''
        sliced = arr[
            box[0][0] : box[1][0] + 1,
            box[0][1] : box[1][1] + 1,
            box[0][2] : box[1][2] + 1
        ]
        return sliced

    def __get_slice_from_zarr_three_d_arr_gbs(self, arr: zarr.core.Array, box: Tuple[Tuple[int, int, int], Tuple[int, int, int]]):
        # TODO: check if slice is correct and equal to : notation slice
        sliced = arr.get_basic_selection(
            (
                slice(box[0][0], box[1][0] + 1),
                slice(box[0][1], box[1][1] + 1),
                slice(box[0][2], box[1][2] + 1)
            )
        )
        return sliced

    def __get_slice_from_zarr_three_d_arr_dask(self, arr: zarr.core.Array, box: Tuple[Tuple[int, int, int], Tuple[int, int, int]]):
        # TODO: check if slice is correct and equal to : notation slice
        # 4: dask slicing: https://github.com/zarr-developers/zarr-python/issues/478#issuecomment-531148674
        zd = da.from_array(arr, chunks=arr.chunks)
        sliced = zd[
            box[0][0] : box[1][0] + 1,
            box[0][1] : box[1][1] + 1,
            box[0][2] : box[1][2] + 1
        ]
        return sliced.compute()

    def __get_slice_from_zarr_three_d_arr_dask_from_zarr(self, arr: zarr.core.Array, box: Tuple[Tuple[int, int, int], Tuple[int, int, int]]):
        zd = da.from_zarr(arr, chunks=arr.chunks)
        sliced = zd[
            box[0][0] : box[1][0] + 1,
            box[0][1] : box[1][1] + 1,
            box[0][2] : box[1][2] + 1
        ]
        return sliced.compute()

    def __get_slice_from_zarr_three_d_arr_tensorstore(self, arr: zarr.core.Array, box: Tuple[Tuple[int, int, int], Tuple[int, int, int]]):
        # TODO: check if slice is correct and equal to : notation slice
        # TODO: await? # store - future object, result - ONE of the ways how to get it sync (can be async)
        # store.read() - returns everything as future object. again result() or other methods
        # can be store[1:10].read() ...
        
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
            box[0][0] : box[1][0] + 1,
            box[0][1] : box[1][1] + 1,
            box[0][2] : box[1][2] + 1
        ].read().result()
        return sliced

    def __get_path_to_zarr_object(self, zarr_obj: Union[zarr.hierarchy.Group, zarr.core.Array]) -> Path:
        '''
        Returns Path to zarr object (array or group)
        '''
        path: Path = Path(zarr_obj.store.path).resolve() / zarr_obj.path
        return path
