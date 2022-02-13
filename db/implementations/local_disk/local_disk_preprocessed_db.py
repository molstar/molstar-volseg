import numpy as np
from pathlib import Path
import h5py
import json
import zarr
import numcodecs

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
        return Path(__file__).parents[1] / 'db' / namespace / key

    async def contains(self, namespace: str, key: str) -> bool:
        '''
        Checks if DB entry exists
        '''
        return self.__path_to_object__(namespace, key).is_file()

    async def store(self, namespace: str, key: str, value: object) -> bool:
        '''
        Takes processed data (returned by preprocessor) as argument 
        '''
        return True

    # TODO: evaluate passing a dict instead of 4 params
    async def read(self, namespace: str, key: str, lattice_id: int, down_sampling_ratio: int) -> IPreprocessedVolume:
        '''
        Reads specific (down)sampling of segmentation data from specific entry from DB
        based on key (e.g. EMD-1111), lattice_id (e.g. 0), and downsampling ratio
        (1 => original data, 2 => downsampled by factor of 2 etc.)
        Returns LocalDiskPreprocessedVolume instance. 
        '''
        path: Path = self.__path_to_object__(namespace=namespace, key=key)
        # Open already created zip store with internal zarr
        store: zarr.storage.ZipStore = zarr.ZipStore(path, mode='r')
        # Re-create zarr hierarchy from opened store
        root: zarr.hierarchy.group = zarr.group(store=store)
        read_zarr_arr: np.ndarray = root.lattice_list[lattice_id][down_sampling_ratio]
        return LocalDiskPreprocessedVolume(read_zarr_arr)

    async def read_metadata(self, namespace: str, key: str) -> IPreprocessedMetadata:
        read_json_of_metadata = ""  # read the same way you read until now
        return LocalDiskPreprocessedMetadata(read_json_of_metadata)
