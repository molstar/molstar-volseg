import base64
import logging
import math
import zlib
from pathlib import Path

import h5py
import numcodecs
import numpy as np
import zarr
from cellstar_preprocessor.flows.common import (
    chunk_numpy_arr,
    create_dataset_wrapper,
    decide_np_dtype,
)
from cellstar_preprocessor.flows.segmentation.category_set_downsampling_methods import (
    store_downsampling_levels_in_zarr,
)
from cellstar_preprocessor.flows.segmentation.downsampling_level_dict import (
    DownsamplingLevelDict,
)
from cellstar_preprocessor.flows.segmentation.segmentation_set_table import (
    SegmentationSetTable,
)
from cellstar_preprocessor.model.segmentation import InternalSegmentation
from cellstar_preprocessor.model.volume import InternalVolume
from sfftkrw.schema.adapter_v0_8_0_dev1 import SFFSegmentation
from vedo import Mesh

temp_zarr_structure_path = None


def check_if_omezarr_has_labels(i: InternalVolume | InternalSegmentation):
    ome_zarr_root = zarr.open_group(i.volume_input_path)
    if "labels" in ome_zarr_root:
        return True
    else:
        return False


def open_hdf5_as_segmentation_object(file_path: Path) -> SFFSegmentation:
    return SFFSegmentation.from_file(str(file_path.resolve()))


def extract_raw_annotations_from_sff(segm_file_path: Path) -> dict:
    """Returns dict of annotation metadata (some fields are removed)"""
    segm_obj = open_hdf5_as_segmentation_object(segm_file_path)
    segm_dict = segm_obj.as_json()
    for lattice in segm_dict["lattice_list"]:
        del lattice["data"]
    for segment in segm_dict["segment_list"]:
        # mesh list with list of ids
        segment["mesh_list"] = [x["id"] for x in segment["mesh_list"]]

    return segm_dict


def hdf5_to_zarr(internal_segmentation: InternalSegmentation):
    """
    Creates temp zarr structure mirroring that of hdf5
    """
    global temp_zarr_structure_path
    temp_zarr_structure_path = internal_segmentation.intermediate_zarr_structure_path
    file_path = internal_segmentation.segmentation_input_path
    try:
        # assert temp_zarr_structure_path.exists() == False, \
        #     f'temp_zarr_structure_path: {temp_zarr_structure_path} already exists'
        # store: zarr.storage.DirectoryStore = zarr.DirectoryStore(str(temp_zarr_structure_path))
        # # directory store does not need to be closed, zip does
        hdf5_file: h5py.File = h5py.File(file_path, mode="r")
        hdf5_file.visititems(__visitor_function)
        hdf5_file.close()
    except Exception as e:
        logging.error(e, stack_info=True, exc_info=True)
        raise e


def __visitor_function(name: str, node: h5py.Dataset) -> None:
    """
    Helper function used to create zarr hierarchy based on hdf5 hierarchy from sff file
    Takes nodes one by one and depending of their nature (group/object dataset/non-object dataset)
    creates the corresponding zarr hierarchy element (group/array)
    """
    global temp_zarr_structure_path
    # input hdf5 file may be too large for memory, so we save it in temp storage
    node_name = node.name[1:]
    if isinstance(node, h5py.Dataset):
        # for text-based fields, including lattice data (as it is b64 encoded zlib-zipped sequence)
        if node.dtype == "object":
            data = [node[()]]
            arr = zarr.array(data, dtype=node.dtype, object_codec=numcodecs.MsgPack())
            zarr.save_array(
                temp_zarr_structure_path / node_name,
                arr,
                object_codec=numcodecs.MsgPack(),
            )
        else:
            arr = zarr.open_array(
                temp_zarr_structure_path / node_name,
                mode="w",
                shape=node.shape,
                dtype=node.dtype,
            )
            arr[...] = node[()]
    elif isinstance(node, h5py.Group):
        zarr.open_group(temp_zarr_structure_path / node_name, mode="w")
    else:
        raise Exception("h5py node is neither dataset nor group")


def lattice_data_to_np_arr(
    data: str, mode: str, endianness: str, arr_shape: tuple[int, int, int]
) -> np.ndarray:
    """
    Converts lattice data to np array.
    Under the hood, decodes lattice data into zlib-zipped data, decompress it to bytes,
    and converts to np arr based on dtype (sff mode), endianness and shape (sff size)
    """
    try:
        decoded_data = base64.b64decode(data)
        byteseq = zlib.decompress(decoded_data)
        np_dtype = decide_np_dtype(mode=mode, endianness=endianness)
        arr = np.frombuffer(byteseq, dtype=np_dtype).reshape(arr_shape, order="F")
    except Exception as e:
        logging.error(e, stack_info=True, exc_info=True)
        raise e
    return arr


def decode_base64_data(data: str, mode: str, endianness: str):
    try:
        # TODO: decode any data, take into account endiannes
        decoded_data = base64.b64decode(data)
        np_dtype = decide_np_dtype(mode=mode, endianness=endianness)
        arr = np.frombuffer(decoded_data, dtype=np_dtype)
    except Exception as e:
        logging.error(e, stack_info=True, exc_info=True)
        raise e
    return arr


def map_value_to_segment_id(zarr_structure):
    """
    Iterates over zarr structure and returns dict with
    keys=lattice_id, and for each lattice id => keys=grid values, values=segm ids
    """
    root = zarr_structure
    d = {}
    for segment_name, segment in root.segment_list.groups():
        lat_id = str(segment.three_d_volume.lattice_id[...])
        value = int(segment.three_d_volume.value[...])
        segment_id = int(segment.id[...])
        if lat_id not in d:
            d[lat_id] = {}
        d[lat_id][value] = segment_id
    # print(d)
    return d


def store_segmentation_data_in_zarr_structure(
    original_data: np.ndarray,
    lattice_data_group: zarr.hierarchy.Group,
    value_to_segment_id_dict_for_specific_lattice_id: dict,
    params_for_storing: dict,
):
    # TODO: params
    # TODO: procedure from create_category_set_downsamplings
    # table with just singletons, e.g. "104": {104}, "94" :{94}
    initial_set_table = SegmentationSetTable(
        original_data, value_to_segment_id_dict_for_specific_lattice_id
    )

    # just x1 downsampling lvl dict
    levels = [
        DownsamplingLevelDict(
            {"ratio": 1, "grid": original_data, "set_table": initial_set_table}
        )
    ]

    # store levels list in zarr structure (can be separate function)
    store_downsampling_levels_in_zarr(
        levels,
        lattice_data_group,
        params_for_storing=params_for_storing,
        time_frame="0",
    )


def write_mesh_component_data_to_zarr_arr(
    target_group: zarr.hierarchy.group,
    mesh: zarr.hierarchy.group,
    mesh_component_name: str,
    params_for_storing: dict,
):
    unchunked_component_data = decode_base64_data(
        data=mesh[mesh_component_name].data[...][0],
        mode=mesh[mesh_component_name].mode[...][0],
        endianness=mesh[mesh_component_name].endianness[...][0],
    )
    # chunked onto triples
    chunked_component_data = chunk_numpy_arr(unchunked_component_data, 3)

    component_arr = create_dataset_wrapper(
        zarr_group=target_group,
        data=chunked_component_data,
        name=mesh_component_name,
        shape=chunked_component_data.shape,
        dtype=chunked_component_data.dtype,
        params_for_storing=params_for_storing,
    )

    component_arr.attrs[f"num_{mesh_component_name}"] = int(
        mesh[mesh_component_name][f"num_{mesh_component_name}"][...]
    )


def make_simplification_curve(n_levels: int, levels_per_order: int) -> dict[int, float]:
    result = {}
    for i in range(n_levels):
        ratio = 10 ** (-i / levels_per_order)
        result[i + 1] = _round_to_significant_digits(ratio, 2)
    return result


def _round_to_significant_digits(number: float, digits: int) -> float:
    first_digit = -math.floor(math.log10(number))
    return round(number, first_digit + digits - 1)


def compute_vertex_density(mesh_list_group: zarr.hierarchy.group, mode="area"):
    """Takes as input mesh list group with stored original lvl meshes.
    Returns estimate of vertex_density for mesh list"""
    mesh_list = []
    total_vertex_count = 0
    for mesh_name, mesh in mesh_list_group.groups():
        mesh_list.append(mesh)
        total_vertex_count = total_vertex_count + mesh.attrs["num_vertices"]

    if mode == "area":
        total_area = 0
        for mesh in mesh_list:
            total_area = total_area + mesh.attrs["area"]

        return total_vertex_count / total_area

        # elif mode == 'volume':
        #     total_volume = 0
        #     for mesh in mesh_list:
        #         total_volume = total_volume + mesh.attrs['volume']

        return total_vertex_count / total_volume


def _convert_mesh_to_vedo_obj(mesh_from_zarr):
    vertices = mesh_from_zarr.vertices[...]
    triangles = mesh_from_zarr.triangles[...]
    vedo_mesh_obj = Mesh([vertices, triangles])
    return vedo_mesh_obj


def _decimate_vedo_obj(vedo_obj, ratio):
    return vedo_obj.decimate(fraction=ratio)


def _get_mesh_data_from_vedo_obj(vedo_obj):
    d = {"arrays": {}, "attrs": {}}
    # NOTE: for old version of vedo
    # d["arrays"]["vertices"] = np.array(vedo_obj.points(), dtype=np.float32)
    # d["arrays"]["triangles"] = np.array(vedo_obj.faces(), dtype=np.int32)
    # d["arrays"]["normals"] = np.array(vedo_obj.normals(), dtype=np.float32)
    d["arrays"]["vertices"] = np.array(vedo_obj.vertices, dtype=np.float32)
    d["arrays"]["triangles"] = np.array(vedo_obj.cells, dtype=np.int32)
    d["arrays"]["normals"] = np.array(vedo_obj.cell_normals, dtype=np.float32)

    d["attrs"]["area"] = vedo_obj.area()
    # d['attrs']['volume'] = vedo_obj.volume()
    d["attrs"]["num_vertices"] = len(d["arrays"]["vertices"])

    return d


def store_mesh_data_in_zarr(
    mesh_data_dict,
    segment: zarr.hierarchy.group,
    detail_level: int,
    # time_frame: str,
    # channel: str,
    params_for_storing: dict,
):
    # zarr group for that detail lvl
    resolution_gr = segment.create_group(str(detail_level))
    # time_gr = resolution_gr.create_group(time_frame)
    # channel_gr = time_gr.create_group(channel)

    d = mesh_data_dict
    for mesh_id in d:
        single_mesh_group = resolution_gr.create_group(str(mesh_id))

        for array_name, array in d[mesh_id]["arrays"].items():
            dset = create_dataset_wrapper(
                zarr_group=single_mesh_group,
                data=array,
                name=array_name,
                shape=array.shape,
                dtype=array.dtype,
                params_for_storing=params_for_storing,
            )

            dset.attrs[f"num_{array_name}"] = len(array)

        for attr_name, attr_val in d[mesh_id]["attrs"].items():
            single_mesh_group.attrs[attr_name] = attr_val

    return resolution_gr


def simplify_meshes(
    mesh_list_group: zarr.hierarchy.Group, ratio: float, segment_id: int
):
    """Returns dict with mesh data for each mesh in mesh list"""
    # for each mesh
    # construct vedo mesh object
    # decimate it
    # get vertices and triangles back
    d = {}
    for mesh_id, mesh in mesh_list_group.groups():
        vedo_obj = _convert_mesh_to_vedo_obj(mesh)
        decimated_vedo_obj = _decimate_vedo_obj(vedo_obj, ratio)
        mesh_data = _get_mesh_data_from_vedo_obj(decimated_vedo_obj)
        d[mesh_id] = mesh_data
    return d
