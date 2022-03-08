import shutil
from typing import Dict, Tuple
import numpy as np
from pathlib import Path
import json
import zarr
from sys import stdout
import numpy as np
import dask.array as da
from timeit import default_timer as timer

from preprocessor.implementations.sff_preprocessor import METADATA_FILENAME, SEGMENTATION_DATA_GROUPNAME, VOLUME_DATA_GROUPNAME

from .local_disk_preprocessed_medata import LocalDiskPreprocessedMetadata
from .local_disk_preprocessed_volume import LocalDiskPreprocessedVolume
from db.interface.i_preprocessed_db import IPreprocessedDb
from db.interface.i_preprocessed_volume import IPreprocessedVolume
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
        return self.__path_to_object__(namespace, key).is_file()
    
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
        temp_store: zarr.storage.DirectoryStore = zarr.DirectoryStore(temp_store_path)
        # perm_store = zarr.ZipStore(self.__path_to_object__(namespace, key) + '.zip', mode='w', compression=12)
        perm_store = zarr.DirectoryStore(self.__path_to_object__(namespace, key))
        zarr.copy_store(temp_store, perm_store, log=stdout)

        # TODO: shutil should work with Path objects, but just in case
        shutil.copy2(temp_store_path / METADATA_FILENAME, self.__path_to_object__(namespace, key) / METADATA_FILENAME)

        # TODO: check if temp dir will be correctly removed and read at the beginning, given that there is a JSON file inside
        # temp_store.close()
        # perm_store.close()
        temp_store.rmdir()
        # TODO: check if copied and store closed properly
        return True

    # TODO: evaluate passing a dict instead of 4 params
    async def read(self, namespace: str, key: str, lattice_id: int, down_sampling_ratio: int) -> IPreprocessedVolume:
        '''
        Deprecated.
        Reads specific (down)sampling of segmentation data from specific entry from DB
        based on key (e.g. EMD-1111), lattice_id (e.g. 0), and downsampling ratio
        (1 => original data, 2 => downsampled by factor of 2 etc.)
        '''
        print('This method is deprecated, please use read_slice method instead')
        path: Path = self.__path_to_object__(namespace=namespace, key=key)
        store: zarr.storage.DirectoryStore = zarr.DirectoryStore(path)
        # Re-create zarr hierarchy from opened store
        root: zarr.hierarchy.group = zarr.group(store=store)
        
        read_segm_arr: np.ndarray = root[SEGMENTATION_DATA_GROUPNAME][lattice_id]
        read_volume_arr: np.ndarray = root[VOLUME_DATA_GROUPNAME]
        # TODO: rewrite return when LocalDiskPreprocessedVolume is changed to Pydantic/built-in data model
        # both volume and segm data
        return {
            'segmentation': read_segm_arr,
            'volume': read_volume_arr
        }

    async def read_slice(self, namespace: str, key: str, lattice_id: int, down_sampling_ratio: int, box: Tuple[Tuple[int, int, int], Tuple[int, int, int]], mode: str) -> IPreprocessedVolume:
        '''
        Reads a slice from a specific (down)sampling of segmentation and volume data
        from specific entry from DB based on key (e.g. EMD-1111), lattice_id (e.g. 0),
        downsampling ratio (1 => original data, 2 => downsampled by factor of 2 etc.),
        and slice box (vec3, vec3) 
        '''
        path: Path = self.__path_to_object__(namespace=namespace, key=key)
        store: zarr.storage.DirectoryStore = zarr.DirectoryStore(path)
        # Re-create zarr hierarchy from opened store
        root: zarr.hierarchy.group = zarr.group(store=store)
        segm_arr: zarr.core.Array = root[SEGMENTATION_DATA_GROUPNAME][lattice_id][down_sampling_ratio]
        volume_arr: zarr.core.Array = root[VOLUME_DATA_GROUPNAME][down_sampling_ratio]
        
        segm_slice = None
        volume_slice = None
        start = timer()
        if mode == 'np':
            # 1: numpy slicing (default)
            segm_slice: np.ndarray = self.__get_slice_from_np_three_d_arr(arr=segm_arr, box=box)
            volume_slice: np.ndarray = self.__get_slice_from_np_three_d_arr(arr=volume_arr, box=box)
        elif mode =='zarr_colon':
            # 2: zarr slicing via : notation
            segm_slice: np.ndarray = self.__get_slice_from_zarr_three_d_arr(arr=segm_arr, box=box)
            volume_slice: np.ndarray = self.__get_slice_from_zarr_three_d_arr(arr=volume_arr, box=box)
        elif mode == 'zarr_gbs':
            # 3: zarr slicing via get_basic_selection and python slices
            segm_slice: np.ndarray = self.__get_slice_from_zarr_three_d_arr_gbs(arr=segm_arr, box=box)
            volume_slice: np.ndarray = self.__get_slice_from_zarr_three_d_arr_gbs(arr=volume_arr, box=box)
        elif mode == 'dask':
            # 4: dask slicing: https://github.com/zarr-developers/zarr-python/issues/478#issuecomment-531148674
            segm_slice: np.ndarray = self.__get_slice_from_zarr_three_d_arr_dask(arr=segm_arr, box=box)
            volume_slice: np.ndarray = self.__get_slice_from_zarr_three_d_arr_dask(arr=volume_arr, box=box)
            
        elif mode == 'dask_from_zarr':
            pass
        #     # 5: dask array from zarr? https://github.com/zarr-developers/zarr-python/issues/843
        #     # Using dask to slice the store with steps (dask.array.from_zarr(store)[::512].compute())
        #     # maybe compute() is not necessary
        #     segm_slice: np.ndarray = self.__get_slice_from_zarr_three_d_arr_dask_from_zarr(arr=segm_arr, box=box)
        #     volume_slice: np.ndarray = self.__get_slice_from_zarr_three_d_arr_dask_from_zarr(arr=volume_arr, box=box)
        elif mode == 'tensorstore ':
            # https://stackoverflow.com/questions/64924224/getting-a-view-of-a-zarr-array-slice
            pass
        
        end = timer()
        print(f'read_slice with mode {mode}: {end - start}')

        # TODO: rewrite when LocalDiskPreprocessedVolume is changed to Pydantic/built-in data model
        # both volume and segm data
        return {
            'segmentation_slice': segm_slice,
            'volume_slice': volume_slice
        }

    async def read_metadata(self, namespace: str, key: str) -> IPreprocessedMetadata:
        path: Path = self.__path_to_object__(namespace=namespace, key=key) / 'metadata.json'
        with open(path.resolve(), 'r', encoding='utf-8') as f:
            # reads into dict
            read_json_of_metadata: Dict = json.load(f)
        return LocalDiskPreprocessedMetadata(read_json_of_metadata)

    def __get_slice_from_np_three_d_arr(self, arr: np.ndarray, box: Tuple[Tuple[int, int, int], Tuple[int, int, int]]) -> np.ndarray:
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
    
    def __get_slice_from_zarr_three_d_arr(self, arr: zarr.core.Array, box: Tuple[Tuple[int, int, int], Tuple[int, int, int]]):
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
        zd = da.from_array(arr)
        sliced = zd[
            box[0][0] : box[1][0] + 1,
            box[0][1] : box[1][1] + 1,
            box[0][2] : box[1][2] + 1
        ]
        return sliced

    def __get_slice_from_zarr_three_d_arr_dask_from_zarr(self, arr: zarr.core.Array, box: Tuple[Tuple[int, int, int], Tuple[int, int, int]]):
        '''
        deprecated
        '''
        # TODO: check if slice is correct and equal to : notation slice
        # dask.array.from_zarr(store)[::512].compute()
        zd = da.array.from_zarr(store)[::512]
        sliced = zd[
            box[0][0] : box[1][0] + 1,
            box[0][1] : box[1][1] + 1,
            box[0][2] : box[1][2] + 1
        ]
        return sliced
