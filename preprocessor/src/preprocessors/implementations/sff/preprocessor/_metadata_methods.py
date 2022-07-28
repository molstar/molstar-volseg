import json
from decimal import Decimal
from pathlib import Path
from typing import TypedDict

import numpy as np
import zarr

from preprocessor.src.preprocessors.implementations.sff.preprocessor.constants import VOLUME_DATA_GROUPNAME, \
    SEGMENTATION_DATA_GROUPNAME
from preprocessor.src.preprocessors.implementations.sff.preprocessor._sfftk_methods import \
    open_hdf5_as_segmentation_object
from preprocessor.src.preprocessors.implementations.sff.preprocessor._volume_map_methods import ccp4_words_to_dict_mrcfile

class MeshMetadata(TypedDict):
    num_vertices: int
    num_triangles: int
    num_normals: int

class MeshListMetadata(TypedDict):
    mesh_ids: dict[int, MeshMetadata]

class DetailLvlsMetadata(TypedDict):
    detail_lvls: dict[int, MeshListMetadata]

class MeshComponentNumbers(TypedDict):
    segment_ids: dict[int, DetailLvlsMetadata]


def extract_annotations(segm_file_path: Path) -> dict:
    '''Returns processed dict of annotation metadata (some fields are removed)'''
    segm_obj = open_hdf5_as_segmentation_object(segm_file_path)
    segm_dict = segm_obj.as_json()
    for lattice in segm_dict['lattice_list']:
        del lattice['data']
    for segment in segm_dict['segment_list']:
        # mesh list with list of ids
        segment['mesh_list'] = [x['id'] for x in segment['mesh_list']]

    return segm_dict


def extract_metadata(zarr_structure: zarr.hierarchy.group, mrc_header: object, mesh_simplification_curve: list[tuple[int, float]]) -> dict:
    root = zarr_structure
    details = ''
    if 'details' in root:
        # temp hack, for some reason emd-1181 instead of empty string has int here
        if isinstance(root.details[...][0], int):
            details = root.details[...][0]
        else:
            details = root.details[...][0].decode('utf-8')
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
        mean_val = str(np.mean(arr_view))
        std_val = str(np.std(arr_view))
        max_val = str(arr_view.max())
        min_val = str(arr_view.min())
        grid_dimensions_val: tuple[int, int, int] = arr.shape

        mean_dict[str(arr_name)] = mean_val
        std_dict[str(arr_name)] = std_val
        max_dict[str(arr_name)] = max_val
        min_dict[str(arr_name)] = min_val
        grid_dimensions_dict[str(arr_name)] = grid_dimensions_val

    lattice_dict = {}
    lattice_ids = []
    mesh_comp_num: MeshComponentNumbers = {}
    detail_lvl_to_fraction_dict = {}
    if SEGMENTATION_DATA_GROUPNAME in root:
        if root.primary_descriptor[0] == b'three_d_volume':
            for gr_name, gr in root[SEGMENTATION_DATA_GROUPNAME].groups():
                # each key is lattice id
                lattice_id = int(gr_name)

                segm_downsamplings = sorted(gr.group_keys())
                # convert to ints
                segm_downsamplings = sorted([int(x) for x in segm_downsamplings])

                lattice_dict[lattice_id] = segm_downsamplings
                lattice_ids.append(lattice_id)
        elif root.primary_descriptor[0] == b'mesh_list':
            mesh_comp_num['segment_ids'] = {}
            for segment_id, segment in root[SEGMENTATION_DATA_GROUPNAME].groups():
                mesh_comp_num['segment_ids'][segment_id] = {
                    'detail_lvls': {}
                }
                for detail_lvl, mesh_list in segment.groups():
                    mesh_comp_num['segment_ids'][segment_id]['detail_lvls'][detail_lvl] = {
                        'mesh_ids': {}
                    }
                    for mesh_id, mesh in mesh_list.groups():
                        mesh_comp_num['segment_ids'][segment_id]['detail_lvls'][detail_lvl]['mesh_ids'][mesh_id] = {}
                        for mesh_component_name, mesh_component in mesh.arrays():
                            d_ref = mesh_comp_num['segment_ids'][segment_id]['detail_lvls'][detail_lvl]['mesh_ids'][mesh_id]
                            d_ref[f'num_{mesh_component_name}'] = mesh_component.attrs[f'num_{mesh_component_name}']

            # adds original detail lvl
            detail_lvl_to_fraction_dict = {1: 1.0}
            detail_lvl_to_fraction_dict.update(dict(mesh_simplification_curve))
                            


    d = ccp4_words_to_dict_mrcfile(mrc_header)

    original_voxel_size: tuple[float, float, float] = (
        d['xLength'] / d['NC'],
        d['yLength'] / d['NR'],
        d['zLength'] / d['NS']
    )

    voxel_sizes_in_downsamplings: dict = {}
    for rate in volume_downsamplings:
        voxel_sizes_in_downsamplings[rate] = tuple(
            [float(Decimal(i) * Decimal(rate)) for i in original_voxel_size]
        )

    # get origin of grid based on NC/NR/NSSTART variables (5, 6, 7) and original voxel size
    # Converting to strings, then to floats to make it JSON serializable (decimals are not) -> ??
    origin: tuple[float, float, float] = (
        float(str(d['NCSTART'] * original_voxel_size[0])),
        float(str(d['NRSTART'] * original_voxel_size[1])),
        float(str(d['NSSTART'] * original_voxel_size[2])),
    )

    # get grid dimensions based on NX/NC, NY/NR, NZ/NS variables (words 1, 2, 3) in CCP4 file
    # original_grid_dimensions: Tuple[int, int, int] = (d['NC'], d['NR'], d['NS'])

    return {
        'general': {
            'details': details
        },
        'volumes': {
            'volume_downsamplings': volume_downsamplings,
            # downsamplings have different voxel size so it is a dict
            'voxel_size': voxel_sizes_in_downsamplings,
            'origin': origin,
            'grid_dimensions': (d['NC'], d['NR'], d['NS']),
            'sampled_grid_dimensions': grid_dimensions_dict,
            'mean': mean_dict,
            'std': std_dict,
            'max': max_dict,
            'min': min_dict
        },
        'segmentation_lattices': {
            'segmentation_lattice_ids': lattice_ids,
            'segmentation_downsamplings': lattice_dict
        },
        'segmentation_meshes': {
            'mesh_component_numbers': mesh_comp_num,
            'detail_lvl_to_fraction': detail_lvl_to_fraction_dict
        }
    }


def temp_save_metadata(metadata: dict, metadata_filename: Path, temp_dir_path: Path) -> None:
    with (temp_dir_path / metadata_filename).open('w') as fp:
        json.dump(metadata, fp, indent=4)
