from argparse import ArgumentError
import logging
from typing import Dict, Tuple, Union
from pathlib import Path
import zarr
from sys import stdout
import numpy as np
import dask.array as da
from timeit import default_timer as timer
import tensorstore as ts
from db.implementations.local_disk.local_disk_preprocessed_db import normalize_box

from preprocessor.src.preprocessors.implementations.sff.preprocessor.constants import SEGMENTATION_DATA_GROUPNAME, \
    VOLUME_DATA_GROUPNAME
from preprocessor.src.preprocessors.implementations.sff.preprocessor.sff_preprocessor import ANNOTATION_METADATA_FILENAME, GRID_METADATA_FILENAME


from db.interface.i_preprocessed_db import IPreprocessedDb, ProcessedVolumeSliceData


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

    async def read_slice(self, lattice_id: int, down_sampling_ratio: int, box: Tuple[Tuple[int, int, int], Tuple[int, int, int]], mode: str = 'dask', timer_printout=False) -> ProcessedVolumeSliceData:
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
            if SEGMENTATION_DATA_GROUPNAME in root:
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

    def close(self):
        self.store.close()

    def __enter__(self):
        return self

    def __exit__(self):
        # TODO: perform check if store has close method, if yes - use it, if not don't
        # in other exit funcs too
        self.store.close()
    
    def __aenter__(self):
        return self

    def __aexit__(self):
        self.store.close()

    def __init__(self, db: IPreprocessedDb, key: str, namespace: str):
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
