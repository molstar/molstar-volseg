from decimal import Decimal
import logging
import math
from typing import Dict, List
from vedo import Mesh
from ._category_set_downsampling_methods import *
from preprocessor.src.preprocessors.implementations.sff.downsampling_level_dict import DownsamplingLevelDict
from preprocessor.src.preprocessors.implementations.sff.preprocessor.constants import DOWNSAMPLING_KERNEL
from preprocessor.src.preprocessors.implementations.sff.segmentation_set_table import SegmentationSetTable
from scipy import signal, ndimage
import dask.array as da
from dask_image.ndfilters import convolve as dask_convolve


def compute_vertex_density(mesh_list_group: zarr.hierarchy.group, mode='area'):
    '''Takes as input mesh list group with stored original lvl meshes.
    Returns estimate of vertex_density for mesh list'''
    mesh_list = []
    total_vertex_count = 0
    for mesh_name, mesh in mesh_list_group.groups():
        mesh_list.append(mesh)
        total_vertex_count = total_vertex_count + mesh.attrs['num_vertices']

    if mode == 'area':
        total_area = 0
        for mesh in mesh_list:
            total_area = total_area + mesh.attrs['area']
        
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
    d = {
        'arrays': {},
        'attrs': {}
    }
    d['arrays']['vertices'] = np.array(vedo_obj.points(), dtype=np.float32)
    d['arrays']['triangles'] = np.array(vedo_obj.faces(), dtype=np.int32)
    d['arrays']['normals'] = np.array(vedo_obj.normals(), dtype=np.float32)
    d['attrs']['area'] = vedo_obj.area()
    # d['attrs']['volume'] = vedo_obj.volume()
    d['attrs']['num_vertices'] = len(d['arrays']['vertices'])

    return d

def _store_mesh_data_in_zarr(mesh_data_dict, segment: zarr.hierarchy.group, ratio, params_for_storing: dict):
    # zarr group for that detail lvl
    new_segment_list_group = segment.create_group(str(ratio))
    d = mesh_data_dict
    for mesh_id in d:
        single_mesh_group = new_segment_list_group.create_group(str(mesh_id))

        for array_name, array in d[mesh_id]['arrays'].items():
            dset = create_dataset_wrapper(
                zarr_group=single_mesh_group,
                data=array,
                name=array_name,
                shape=array.shape,
                dtype=array.dtype,
                params_for_storing=params_for_storing
            )

            dset.attrs[f'num_{array_name}'] = len(array)
            
        
        for attr_name, attr_val in d[mesh_id]['attrs'].items():
            single_mesh_group.attrs[attr_name] = attr_val

    return new_segment_list_group
        

def simplify_meshes(mesh_list_group: zarr.hierarchy.Group, ratio: float, segment_id: int):
    '''Returns dict with mesh data for each mesh in mesh list'''
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

# def __store_simplified_mesh_in_zarr(vertices, triangles, normals, simplified_mesh_zarr_gr):
#     # TODO: add attrs (num ...) to arrs to
#     pass

# def create_mesh_simplifications(vertices, triangles, segm_data_gr, num_steps):
#     mesh = Mesh([vertices, triangles])
#     for step in range(1, num_steps + 1):
#         ratio = Decimal(2)**step
#         factor = float(Decimal(1) / ratio)
#         decimated_mesh = mesh.decimate(factor)
#         decimated_normals = np.array(decimated_mesh.normals(), dtype=np.float32)
#         decimated_vertices = np.array(decimated_mesh.points(), dtype=np.float32)
#         decimated_triangles = np.array(decimated_mesh.faces(), dtype=np.int32)
#         # simplified_mesh_zarr_gr = segm_data_gr.create_group(str(ratio))
#         __store_simplified_mesh_in_zarr(
#             vertices=decimated_vertices,
#             triangles=decimated_triangles,
#             normals=decimated_normals,
#             simplified_mesh_zarr_gr=simplified_mesh_zarr_gr
#         )




def compute_number_of_downsampling_steps(min_grid_size: int, input_grid_size: int, force_dtype: type, factor: int,
                                         min_downsampled_file_size_bytes: int = 5 * 10 ** 6) -> int:
    if input_grid_size <= min_grid_size:
        return 1
    # num_of_downsampling_steps: int = math.ceil(math.log2(input_grid_size/min_grid_size))
    x1_filesize_bytes: int = input_grid_size * force_dtype.itemsize
    num_of_downsampling_steps: int = int(math.log(
        x1_filesize_bytes / min_downsampled_file_size_bytes,
        factor
    ))
    if num_of_downsampling_steps <= 1:
        return 1
    return num_of_downsampling_steps


def create_volume_downsamplings(original_data: da.Array, downsampling_steps: int,
                                downsampled_data_group: zarr.hierarchy.Group, params_for_storing: dict, force_dtype=np.float32):
    '''
    Take original volume data, do all downsampling levels and store in zarr struct one by one
    '''
    current_level_data = original_data
    __store_single_volume_downsampling_in_zarr_stucture(current_level_data, downsampled_data_group, 1, params_for_storing=params_for_storing, force_dtype=force_dtype)
    for i in range(downsampling_steps):
        current_ratio = 2 ** (i + 1)
        kernel = generate_kernel_3d_arr(list(DOWNSAMPLING_KERNEL))
        # downsampled_data: np.ndarray = signal.convolve(current_level_data, kernel, mode='same', method='fft')
        # downsampled_data: np.ndarray = ndimage.convolve(current_level_data, kernel, mode='mirror', cval=0.0)
        downsampled_data = dask_convolve(current_level_data, kernel, mode='mirror', cval=0.0)
        downsampled_data = downsampled_data[::2, ::2, ::2]

        __store_single_volume_downsampling_in_zarr_stucture(downsampled_data, downsampled_data_group, current_ratio,
                                                            params_for_storing=params_for_storing,
                                                            force_dtype=force_dtype)
        current_level_data = downsampled_data


def create_category_set_downsamplings(
        magic_kernel: MagicKernel3dDownsampler,
        original_data: np.ndarray,
        downsampling_steps: int,
        downsampled_data_group: zarr.hierarchy.Group,
        value_to_segment_id_dict_for_specific_lattice_id: Dict,
        params_for_storing: dict
):
    '''
    Take original segmentation data, do all downsampling levels, create zarr datasets for each
    '''
    # table with just singletons, e.g. "104": {104}, "94" :{94}
    initial_set_table = SegmentationSetTable(original_data, value_to_segment_id_dict_for_specific_lattice_id)

    # for now contains just x1 downsampling lvl dict, in loop new dicts for new levels are appended
    levels = [
        DownsamplingLevelDict({'ratio': 1, 'grid': original_data, 'set_table': initial_set_table})
    ]
    for i in range(downsampling_steps):
        current_set_table = SegmentationSetTable(original_data, value_to_segment_id_dict_for_specific_lattice_id)
        # on first iteration (i.e. when doing x2 downsampling), it takes original_data and initial_set_table with set of singletons 
        levels.append(downsample_categorical_data(magic_kernel, levels[i], current_set_table))

    # store levels list in zarr structure (can be separate function)
    store_downsampling_levels_in_zarr(levels, downsampled_data_group, params_for_storing=params_for_storing)


def __store_single_volume_downsampling_in_zarr_stucture(downsampled_data: da.Array,
                                                        downsampled_data_group: zarr.hierarchy.Group, ratio: int,
                                                        params_for_storing: dict,
                                                        force_dtype=np.float32):
    
    
    zarr_arr = create_dataset_wrapper(
        zarr_group=downsampled_data_group,
        data=None,
        name=str(ratio),
        shape=downsampled_data.shape,
        dtype=force_dtype,
        params_for_storing=params_for_storing,
        is_empty=True
    )

    da.to_zarr(arr=downsampled_data, url=zarr_arr, overwrite=True, compute=True)
    


def generate_kernel_3d_arr(pattern: List[int]) -> np.ndarray:
    '''
    Generates conv kernel based on pattern provided (e.g. [1,4,6,4,1]).
    https://stackoverflow.com/questions/71739757/generate-3d-numpy-array-based-on-provided-pattern/71742892#71742892
    '''
    try:
        assert len(pattern) == 5, 'pattern should have length 5'
        pattern = pattern[0:3]
        x = np.array(pattern[-1]).reshape([1, 1, 1])
        for p in reversed(pattern[:-1]):
            x = np.pad(x, mode='constant', constant_values=p, pad_width=1)

        k = (1 / x.sum()) * x
        assert k.shape == (5, 5, 5)
    except AssertionError as e:
        logging.error(e, stack_info=True, exc_info=True)
        raise e
    return k
