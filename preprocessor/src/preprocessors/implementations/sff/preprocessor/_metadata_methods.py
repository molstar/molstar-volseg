import json
from decimal import Decimal
from pathlib import Path

import numpy as np
import zarr

from preprocessor.src.preprocessors.implementations.sff.preprocessor.constants import VOLUME_DATA_GROUPNAME, \
    SEGMENTATION_DATA_GROUPNAME
from preprocessor.src.preprocessors.implementations.sff.preprocessor._sfftk_methods import \
    open_hdf5_as_segmentation_object
from preprocessor.src.preprocessors.implementations.sff.preprocessor._volume_map_methods import ccp4_words_to_dict


def extract_annotations(segm_file_path: Path) -> dict:
    '''Returns processed dict of annotation metadata (some fields are removed)'''
    segm_obj = open_hdf5_as_segmentation_object(segm_file_path)
    segm_dict = segm_obj.as_json()
    for lattice in segm_dict['lattice_list']:
        del lattice['data']
    for segment in segm_dict['segment_list']:
        segment['mesh_list'] = [x['id'] for x in segment['mesh_list']]

    return segm_dict


def extract_metadata(zarr_structure: zarr.hierarchy.group, map_object) -> dict:
    root = zarr_structure
    details = ''
    if 'details' in root:
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
        mean_val = str(np.mean(arr[...]))
        std_val = str(np.std(arr[...]))
        max_val = str(arr[...].max())
        min_val = str(arr[...].min())
        grid_dimensions_val: tuple[int, int, int] = arr.shape

        mean_dict[str(arr_name)] = mean_val
        std_dict[str(arr_name)] = std_val
        max_dict[str(arr_name)] = max_val
        min_dict[str(arr_name)] = min_val
        grid_dimensions_dict[str(arr_name)] = grid_dimensions_val

    lattice_dict = {}
    lattice_ids = []
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
            # TODO: extract mesh metadata from zarr: number of triangles, number of simplified meshes
            # then write them to return statement
            pass


    d = ccp4_words_to_dict(map_object)

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
            
        }
    }


def temp_save_metadata(metadata: dict, metadata_filename: Path, temp_dir_path: Path) -> None:
    with (temp_dir_path / metadata_filename).open('w') as fp:
        json.dump(metadata, fp, indent=4)
