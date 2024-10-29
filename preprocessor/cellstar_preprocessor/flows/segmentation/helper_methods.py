import base64
import logging
import math
import zlib
from pathlib import Path
from cellstar_db.models import PreparedMeshData, VedoMeshData
from cellstar_preprocessor.tools.decode_base64_data.decode_base64_data import decode_base64_data
import h5py
import numcodecs
import numpy as np
import zarr
from cellstar_preprocessor.flows.common import chunk_numpy_arr, decide_np_dtype
from cellstar_preprocessor.flows.zarr_methods import create_dataset_wrapper
from cellstar_preprocessor.model.segmentation import InternalSegmentation
from cellstar_preprocessor.model.volume import InternalVolume
from sfftkrw.schema.adapter_v0_8_0_dev1 import SFFSegmentation
from vedo import Mesh
import dask.array as da
temp_zarr_structure_path = None


def check_if_omezarr_has_labels(i: InternalVolume | InternalSegmentation):
    ome_zarr_root = zarr.open_group(i.input_path)
    if "labels" in ome_zarr_root:
        return True
    else:
        return False


def open_hdf5_as_segmentation_object(file_path: Path) -> SFFSegmentation:
    return SFFSegmentation.from_file(str(file_path.resolve()))


def extract_raw_annotations_from_sff(segm_file_path: Path):
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
    temp_zarr_structure_path = internal_segmentation.path
    file_path = internal_segmentation.input_path
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


def get_segmentation_sampling_info(root_data_group, sampling_info_dict):
    for res_gr_name, res_gr in root_data_group.groups():
        # create layers (time gr, channel gr)
        sampling_info_dict.boxes[res_gr_name] = {
            "origin": None,
            "voxel_size": None,
            "grid_dimensions": None,
            # 'force_dtype': None
        }

        for time_gr_name, time_gr in res_gr.groups():
            sampling_info_dict.boxes[res_gr_name][
                "grid_dimensions"
            ] = time_gr.grid.shape


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

# TODO: stotre mesh segmentation data
    # for segment_name, segment in zarr_structure.segment_list.groups():
    #     segment_id = int(segment.id[...])
    #     single_segment_group = timeframe_gr.create_group(segment_id)
    #     single_detail_lvl_group = single_segment_group.create_group(1)
    #     if "mesh_list" in segment:
    #         for mesh_name, mesh in segment.mesh_list.groups():
    #             mesh_id = int(mesh.id[...])
    #             single_mesh_group = single_detail_lvl_group.create_group(mesh_id)

    #             for mesh_component_name, mesh_component in mesh.groups():
    #                 if mesh_component_name != "id":
    #                     write_mesh_component_data_to_zarr_arr(
    #                         target_group=single_mesh_group,
    #                         mesh=mesh,
    #                         mesh_component_name=mesh_component_name,
    #                         params_for_storing=params_for_storing,
    #                     )
    #             # TODO: check in which units is area and volume
    #             vertices = single_mesh_group["vertices"][...]
    #             triangles = single_mesh_group["triangles"][...]
    #             vedo_mesh_obj = Mesh([vertices, triangles])
                # single_mesh_group.attrs["num_vertices"] = (
                #     single_mesh_group.vertices.attrs["num_vertices"]
                # )
                # single_mesh_group.attrs["area"] = vedo_mesh_obj.area()
                # # single_mesh_group.attrs['volume'] = vedo_mesh_obj.volume()

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


def compute_vertex_density(prepared_mesh_data: PreparedMeshData):
    """Takes as input mesh list group with stored original lvl meshes.
    Returns estimate of vertex_density for mesh list"""
    total_vertex_count = prepared_mesh_data.vertices.size
    total_area = prepared_mesh_data.area
    # for mesh in mesh_list:
        # total_area = total_area + mesh.attrs["area"]

    return total_vertex_count / total_area

        # elif mode == 'volume':
        #     total_volume = 0
        #     for mesh in mesh_list:
        #         total_volume = total_volume + mesh.attrs['volume']


def _convert_prepared_mesh_data_to_vedo_obj(prepared_mesh_data: PreparedMeshData):
    # vertices = prepared_mesh_data.vertices.compute()
    # triangles = mesh_from_zarr.triangles[...]
    # TODO: if does not work do .compute()
    vedo_mesh_obj = Mesh([prepared_mesh_data.vertices, prepared_mesh_data.triangles])
    return vedo_mesh_obj


def _decimate_vedo_obj(vedo_obj: Mesh, ratio):
    return vedo_obj.decimate(fraction=ratio)


def _get_mesh_data_from_vedo_obj(vedo_obj: Mesh):
    # should get mesh data (verts, tr, norm) back
    return VedoMeshData(
        vertices=da.from_array(vedo_obj.vertices, dtype=np.float32),
        triangles=da.from_array(vedo_obj.vertices, dtype=np.float32),
        normals=da.from_array(vedo_obj.vertices, dtype=np.float32),
        area=vedo_obj.area()
    )
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


def simplify_mesh(
    prepared_mesh_data: PreparedMeshData, fraction: float
):
    """Returns dict with mesh data for each mesh in mesh list"""
    
    vedo_obj = _convert_prepared_mesh_data_to_vedo_obj(prepared_mesh_data)
    decimated_vedo_obj = _decimate_vedo_obj(vedo_obj, fraction)
    ve = _get_mesh_data_from_vedo_obj(decimated_vedo_obj)
    return PreparedMeshData(
        vertices=ve.vertices,
        triangels=ve.triangles,
        normals=ve.normals,
        area=ve.area,
        segment_id=prepared_mesh_data.segment_id,
        fraction=fraction
    )