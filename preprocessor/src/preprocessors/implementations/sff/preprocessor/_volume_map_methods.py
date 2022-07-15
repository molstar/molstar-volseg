from decimal import getcontext, ROUND_CEILING, Decimal
import logging
from pathlib import Path

import gemmi
import numpy as np


def ccp4_words_to_dict(m: gemmi.Ccp4Map) -> dict:
    ctx = getcontext()
    ctx.rounding = ROUND_CEILING
    d = {}
    d['NC'], d['NR'], d['NS'] = m.header_i32(1), m.header_i32(2), m.header_i32(3)
    d['NCSTART'], d['NRSTART'], d['NSSTART'] = m.header_i32(5), m.header_i32(6), m.header_i32(7)
    d['xLength'] = round(Decimal(m.header_float(11)), 1)
    d['yLength'] = round(Decimal(m.header_float(12)), 1)
    d['zLength'] = round(Decimal(m.header_float(13)), 1)
    d['MAPC'], d['MAPR'], d['MAPS'] = m.header_i32(17), m.header_i32(18), m.header_i32(19)
    return d

def ccp4_words_to_dict_mrcfile(mrc_header: object) -> dict:
    '''input - mrcfile object header (mrc.header)'''
    ctx = getcontext()
    ctx.rounding = ROUND_CEILING
    d = {}

    m = mrc_header
    # mrcfile implementation
    d['NC'], d['NR'], d['NS'] = int(m.nx), int(m.ny), int(m.nz)
    d['NCSTART'], d['NRSTART'], d['NSSTART'] = int(m.nxstart), int(m.nystart), int(m.nzstart)
    d['xLength'] = round(Decimal(m.cella.x), 1)
    d['yLength'] = round(Decimal(m.cella.y), 1)
    d['zLength'] = round(Decimal(m.cella.z), 1)
    d['MAPC'], d['MAPR'], d['MAPS'] = int(m.mapc), int(m.mapr), int(m.maps)

    return d

def read_volume_data(m: gemmi.Ccp4Map, force_dtype=np.float32) -> np.ndarray:
    '''
    Takes read map object (axis normalized upfront) and returns numpy arr with volume data
    '''
    # TODO: can be dask array to save memory?
    arr: np.ndarray = np.array(m.grid, dtype=force_dtype)
    # gemmi assigns columns to 1st numpy dimension, and sections to 3rd
    # but we don't need swapaxes, as slices are requested from
    # frontend in X, Y, Z order (columns 1st)
    # arr = arr.swapaxes(0, 2)
    return arr


def read_and_normalize_map(volume_file_path: Path) -> np.ndarray:
    map_object = read_volume_map_to_object(volume_file_path)
    normalized_axis_map_object = normalize_axis_order(map_object)
    arr = read_volume_data(normalized_axis_map_object)
    return arr


def normalize_axis_order(map_object: gemmi.Ccp4Map):
    '''
    Normalizes axis order to X, Y, Z (1, 2, 3)
    '''
    # just reorders axis to X, Y, Z (https://gemmi.readthedocs.io/en/latest/grid.html#setup)
    map_object.setup(float('nan'), gemmi.MapSetup.ReorderOnly)
    ccp4_header = ccp4_words_to_dict(map_object)
    new_axis_order = ccp4_header['MAPC'], ccp4_header['MAPR'], ccp4_header['MAPS']
    try:
        assert new_axis_order == (1, 2, 3), f'Axis order is {new_axis_order}, should be (1, 2, 3) or X, Y, Z'
    except AssertionError as e:
        # TODO: check if it should be logger instead LATER ON
        logging.error(e, stack_info=True, exc_info=True)
    return map_object


def read_volume_map_to_object(volume_file_path: Path) -> gemmi.Ccp4Map:
    '''
    Reads ccp4 map to gemmi.Ccp4Map object
    '''
    # https://www.ccpem.ac.uk/mrc_format/mrc2014.php
    # https://www.ccp4.ac.uk/html/maplib.html
    return gemmi.read_ccp4_map(str(volume_file_path.resolve()))
