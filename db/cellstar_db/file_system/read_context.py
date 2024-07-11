import json
import logging
from pathlib import Path
from timeit import default_timer as timer
from typing import Literal, Tuple, Union

import dask.array as da
import numpy as np
import tensorstore as ts
import zarr
from cellstar_db.file_system.constants import (
    GEOMETRIC_SEGMENTATION_FILENAME,
    LATTICE_SEGMENTATION_DATA_GROUPNAME,
    MESH_SEGMENTATION_DATA_GROUPNAME,
    QUANTIZATION_DATA_DICT_ATTR_NAME,
    VOLUME_DATA_GROUPNAME,
)
from cellstar_db.models import (
    GeometricSegmentationData,
    LatticeSegmentationSliceData,
    MeshData,
    MeshesData,
    SliceData,
)
from cellstar_db.protocol import DBReadContext, VolumeServerDB
from cellstar_db.utils.box import normalize_box
from cellstar_db.utils.quantization import decode_quantized_data
from fastapi import HTTPException


class FileSystemDBReadContext(DBReadContext):
    async def read_slice(
        self,
        down_sampling_ratio: int,
        box: Tuple[Tuple[int, int, int], Tuple[int, int, int]],
        channel_id: str,
        time: int,
        mode: str = "dask",
        timer_printout=False,
        lattice_id: str = "0",
    ) -> SliceData:
        """
        Reads a slice from a specific (down)sampling of segmentation and volume data
        from specific entry from DB based on key (e.g. EMD-1111), lattice_id (e.g. 0),
        downsampling ratio (1 => original data, 2 => downsampled by factor of 2 etc.),
        and slice box (vec3, vec3)
        """
        try:
            box = normalize_box(box)

            root: zarr.Group = zarr.group(self.store)

            segm_arr = None
            segm_dict = None
            if LATTICE_SEGMENTATION_DATA_GROUPNAME in root and (lattice_id is not None):
                segm_arr = root[LATTICE_SEGMENTATION_DATA_GROUPNAME][lattice_id][
                    down_sampling_ratio
                ][time].grid
                assert (
                    np.array(box[1]) <= np.array(segm_arr.shape)
                ).all(), f"requested box {box} does not correspond to arr dimensions"
                segm_dict = root[LATTICE_SEGMENTATION_DATA_GROUPNAME][lattice_id][
                    down_sampling_ratio
                ][time].set_table[0]
            else:
                raise HTTPException(
                    status_code=404,
                    detail="No segmentation data is available for the the given entry or lattice_id is None",
                )

            if VOLUME_DATA_GROUPNAME in root and (down_sampling_ratio is not None):
                volume_arr: zarr.Array = root[VOLUME_DATA_GROUPNAME][
                    down_sampling_ratio
                ][time][channel_id]
            else:
                raise HTTPException(
                    status_code=404,
                    detail="No volume data is available for the the given entry or down_sampling_ratio is None",
                )

            assert (
                np.array(box[0]) >= np.array([0, 0, 0])
            ).all(), f"requested box {box} does not correspond to arr dimensions"
            assert (
                np.array(box[1]) <= np.array(volume_arr.shape)
            ).all(), f"requested box {box} does not correspond to arr dimensions"

            segm_slice: np.ndarray
            volume_slice: np.ndarray

            start = timer()
            volume_slice = self._do_slicing(arr=volume_arr, box=box, mode=mode)
            if segm_arr:
                segm_slice = self._do_slicing(arr=segm_arr, box=box, mode=mode)
            end = timer()

            # check if volume_arr was originally quantized data (e.g. some attr on array, e.g. data_dict attr with data_dict)
            # if yes, decode volume_slice (reassamble data dict from data_dict attr, just add 'data' key with volume_slice)
            # do .compute on output of decode_quantized_data function if output is da.Array

            if QUANTIZATION_DATA_DICT_ATTR_NAME in volume_arr.attrs:
                data_dict = volume_arr.attrs[QUANTIZATION_DATA_DICT_ATTR_NAME]
                data_dict["data"] = volume_slice
                volume_slice = decode_quantized_data(data_dict)
                if isinstance(volume_slice, da.Array):
                    volume_slice = volume_slice.compute()

            if timer_printout == True:
                print(f"read_slice with mode {mode}: {end - start}")
            d = SliceData(volume_slice=volume_slice, time=time, channel_id=channel_id)
            if segm_arr:
                d.segmentation_slice = LatticeSegmentationSliceData(
                    category_set_ids=segm_slice,
                    category_set_dict=segm_dict,
                    lattice_id=lattice_id,
                )
        except Exception as e:
            logging.error(e, stack_info=True, exc_info=True)
            raise e

        return d

    async def read_meshes(
        self, segmentation_id: str, time: int, segment_id: int, detail_lvl: int
    ) -> MeshesData:
        """
        Returns list of meshes for a given segment, entry, detail lvl
        """
        try:
            mesh_list: MeshesData = []
            root: zarr.Group = zarr.group(self.store)

            # # segmentation_id => timeframe => segment_id => detail_lvl => mesh_id in meshlist
            # mesh_segmentation_data: list[str, dict[int, list[dict[int, list[dict[int, list[dict[int, SingleMeshSegmentationData]]]]]]]]
            mesh_list_group = root[MESH_SEGMENTATION_DATA_GROUPNAME][segmentation_id][
                time
            ][segment_id][detail_lvl]

            for mesh_name, mesh in mesh_list_group.groups():
                mesh_data: MeshData = {"mesh_id": int(mesh_name)}
                for mesh_component_name, mesh_component_arr in mesh.arrays():
                    mesh_data[f"{mesh_component_name}"] = mesh_component_arr[...]
                assert "vertices" in mesh_data
                assert "triangles" in mesh_data
                mesh_list.append(mesh_data)
        except Exception as e:
            logging.error(e, stack_info=True, exc_info=True)
            raise e

        return mesh_list

    async def read_geometric_segmentation(
        self, segmentation_id: str, time: int
    ) -> GeometricSegmentationData:
        try:
            # GeometricSegmentationJson = list[GeometricSegmentationData]
            path: Path = Path(self.store.path).parent / GEOMETRIC_SEGMENTATION_FILENAME
            with open(path.resolve(), "r", encoding="utf-8") as f:
                # reads into dict
                read_json: list[GeometricSegmentationData] = json.load(f)
                filter_results = list(
                    filter(lambda i: i["segmentation_id"] == segmentation_id, read_json)
                )
                assert len(filter_results) == 1
                target_segmentation: GeometricSegmentationData = filter_results[0]
                target_timeframe_data = target_segmentation["primitives"][str(time)]
        except Exception as e:
            logging.error(e, stack_info=True, exc_info=True)
            raise e

        return target_timeframe_data

    async def read_volume_slice(
        self,
        down_sampling_ratio: int,
        box: Tuple[Tuple[int, int, int], Tuple[int, int, int]],
        channel_id: str,
        time: int,
        mode: str = "dask",
        timer_printout=False,
    ) -> SliceData:
        try:
            box = normalize_box(box)

            root: zarr.Group = zarr.group(self.store)

            if VOLUME_DATA_GROUPNAME in root and (down_sampling_ratio is not None):
                volume_arr: zarr.Array = root[VOLUME_DATA_GROUPNAME][
                    down_sampling_ratio
                ][time][channel_id]

                assert (
                    np.array(box[0]) >= np.array([0, 0, 0])
                ).all(), f"requested box {box} does not correspond to arr dimensions"
                assert (
                    np.array(box[1]) <= np.array(volume_arr.shape)
                ).all(), f"requested box {box} does not correspond to arr dimensions"

                start = timer()
                volume_slice = self._do_slicing(arr=volume_arr, box=box, mode=mode)
                end = timer()

                # check if volume_arr was originally quantized data (e.g. some attr on array, e.g. data_dict attr with data_dict)
                # if yes, decode volume_slice (reassamble data dict from data_dict attr, just add 'data' key with volume_slice)
                # do .compute on output of decode_quantized_data function if output is da.Array

                if QUANTIZATION_DATA_DICT_ATTR_NAME in volume_arr.attrs:
                    data_dict = volume_arr.attrs[QUANTIZATION_DATA_DICT_ATTR_NAME]
                    data_dict["data"] = volume_slice
                    volume_slice = decode_quantized_data(data_dict)
                    if isinstance(volume_slice, da.Array):
                        volume_slice = volume_slice.compute()

                if timer_printout == True:
                    print(f"read_volume_slice with mode {mode}: {end - start}")

                return SliceData(
                    volume_slice=volume_slice, time=time, channel_id=channel_id
                )
            else:
                raise HTTPException(
                    status_code=404,
                    detail="No volume data is available for the the given entry or down_sampling_ratio is None",
                )

        except Exception as e:
            logging.error(e, stack_info=True, exc_info=True)
            raise e

    async def read_segmentation_slice(
        self,
        lattice_id: str,
        down_sampling_ratio: int,
        box: Tuple[Tuple[int, int, int], Tuple[int, int, int]],
        time: int,
        mode: str = "dask",
        timer_printout=False,
    ) -> SliceData:
        try:
            box = normalize_box(box)

            root: zarr.Group = zarr.group(self.store)

            segm_arr = None
            segm_dict = None
            if LATTICE_SEGMENTATION_DATA_GROUPNAME in root and (lattice_id is not None):
                segm_arr = root[LATTICE_SEGMENTATION_DATA_GROUPNAME][lattice_id][
                    down_sampling_ratio
                ][time].grid
                assert (
                    np.array(box[1]) <= np.array(segm_arr.shape)
                ).all(), f"requested box {box} does not correspond to arr dimensions"
                segm_dict = root[LATTICE_SEGMENTATION_DATA_GROUPNAME][lattice_id][
                    down_sampling_ratio
                ][time].set_table[0]
            else:
                raise HTTPException(
                    status_code=404,
                    detail="No segmentation data is available for the the given entry or lattice_id is None",
                )

            start = timer()
            segm_slice = self._do_slicing(arr=segm_arr, box=box, mode=mode)
            end = timer()

            if timer_printout == True:
                print(f"read_segmentation_slice with mode {mode}: {end - start}")

            return SliceData(
                segmentation_slice=LatticeSegmentationSliceData(
                    category_set_ids=segm_slice,
                    category_set_dict=segm_dict,
                    lattice_id=lattice_id,
                ),
                time=time,
            )

        except Exception as e:
            logging.error(e, stack_info=True, exc_info=True)
            raise e

    def _do_slicing(
        self,
        arr: zarr.Array,
        box: Tuple[Tuple[int, int, int], Tuple[int, int, int]],
        mode: Literal["zarr_colon", "zarr_gbs", "dask", "dask_from_zarr", "tensorstore"],
    ) -> np.ndarray:
        match mode:
            case "zarr_colon":
                # 2: zarr slicing via : notation
                arr_slice = self.__get_slice_from_zarr_three_d_arr(arr=arr, box=box)
            case "zarr_gbs":
                arr_slice = self.__get_slice_from_zarr_three_d_arr_gbs(arr=arr, box=box)
            case "dask":
                arr_slice = self.__get_slice_from_zarr_three_d_arr_dask(arr=arr, box=box)
            case "dask_from_zarr":
                arr_slice = self.__get_slice_from_zarr_three_d_arr_dask_from_zarr(
                    arr=arr, box=box
                )
            case "tensorstore":
                arr_slice = self.__get_slice_from_zarr_three_d_arr_tensorstore(
                    arr=arr, box=box
                )
            case _:
                raise Exception(f"Slicing mode is not supported: {mode}")

        return arr_slice

    def __get_slice_from_zarr_three_d_arr(
        self,
        arr: zarr.Array,
        box: Tuple[Tuple[int, int, int], Tuple[int, int, int]],
    ):
        """
        Based on (vec3, vec3) tuple (coordinates of corners of the box)
        returns a slice of 3d array
        """
        sliced = arr[
            box[0][0] : box[1][0] + 1,
            box[0][1] : box[1][1] + 1,
            box[0][2] : box[1][2] + 1,
        ]
        return sliced

    def __get_slice_from_zarr_three_d_arr_gbs(
        self,
        arr: zarr.Array,
        box: Tuple[Tuple[int, int, int], Tuple[int, int, int]],
    ):
        # TODO: check if slice is correct and equal to : notation slice
        sliced = arr.get_basic_selection(
            (
                slice(box[0][0], box[1][0] + 1),
                slice(box[0][1], box[1][1] + 1),
                slice(box[0][2], box[1][2] + 1),
            )
        )
        return sliced

    def __get_slice_from_zarr_three_d_arr_dask(
        self,
        arr: zarr.Array,
        box: Tuple[Tuple[int, int, int], Tuple[int, int, int]],
    ):
        # TODO: check if slice is correct and equal to : notation slice
        # 4: dask slicing: https://github.com/zarr-developers/zarr-python/issues/478#issuecomment-531148674
        zd = da.from_array(arr, chunks=arr.chunks)
        sliced = zd[
            box[0][0] : box[1][0] + 1,
            box[0][1] : box[1][1] + 1,
            box[0][2] : box[1][2] + 1,
        ]
        return sliced.compute()

    def __get_slice_from_zarr_three_d_arr_dask_from_zarr(
        self,
        arr: zarr.Array,
        box: Tuple[Tuple[int, int, int], Tuple[int, int, int]],
    ):
        zd = da.from_zarr(arr, chunks=arr.chunks)
        sliced = zd[
            box[0][0] : box[1][0] + 1,
            box[0][1] : box[1][1] + 1,
            box[0][2] : box[1][2] + 1,
        ]
        return sliced.compute()

    def __get_slice_from_zarr_three_d_arr_tensorstore(
        self,
        arr: zarr.Array,
        box: Tuple[Tuple[int, int, int], Tuple[int, int, int]],
    ):
        # TODO: check if slice is correct and equal to : notation slice
        # TODO: await? # store - future object, result - ONE of the ways how to get it sync (can be async)
        # store.read() - returns everything as future object. again result() or other methods
        # can be store[1:10].read() ...
        print("This method is MAY not work properly for ZIP store. Needs to be checked")
        path = self.__get_path_to_zarr_object(arr)
        store = ts.open(
            {
                "driver": "zarr",
                "kvstore": {
                    "driver": "file",
                    "path": str(path.resolve()),
                },
            },
            read=True,
        ).result()
        sliced = (
            store[
                box[0][0] : box[1][0] + 1,
                box[0][1] : box[1][1] + 1,
                box[0][2] : box[1][2] + 1,
            ]
            .read()
            .result()
        )
        return sliced

    def __get_path_to_zarr_object(
        self, zarr_obj: Union[zarr.Group, zarr.Array]
    ) -> Path:
        """
        Returns Path to zarr object (array or group)
        """
        path: Path = Path(zarr_obj.store.path).resolve() / zarr_obj.path
        return path

    def close(self):
        if hasattr(self.store, "close"):
            self.store.close()
        else:
            pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if hasattr(self.store, "close"):
            self.store.close()
        else:
            pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args, **kwargs):
        if hasattr(self.store, "aclose"):
            await self.store.aclose()
        if hasattr(self.store, "close"):
            self.store.close()
        else:
            pass

    def __init__(self, db: VolumeServerDB, namespace: str, key: str):
        self.db = db
        self.path = db.path_to_zarr_root_data(namespace=namespace, key=key)
        assert self.path.exists(), f"Path {self.path} does not exist"
        self.key = key
        self.namespace = namespace
        if self.db.store_type == "directory":
            self.store = zarr.DirectoryStore(path=self.path)
        elif self.db.store_type == "zip":
            self.store = zarr.ZipStore(
                path=self.path, compression=0, allowZip64=True, mode="r"
            )
