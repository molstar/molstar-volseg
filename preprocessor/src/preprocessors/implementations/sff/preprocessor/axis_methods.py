from pathlib import Path

import gemmi



def create_value_to_segment_id_mapping(self, zarr_structure):
    '''
    Iterates over zarr structure and returns dict with
    keys=lattice_id, and for each lattice id => keys=grid values, values=segm ids
    '''
    root = zarr_structure
    d = {}
    for segment_name, segment in root.segment_list.groups():
        lat_id = int(segment.three_d_volume.lattice_id[...])
        value = int(segment.three_d_volume.value[...])
        segment_id = int(segment.id[...])
        if lat_id not in d:
            d[lat_id] = {}
        d[lat_id][value] = segment_id
    # print(d)
    return d

def normalize_axis_order(self, map_object: gemmi.Ccp4Map):
    '''
    Normalizes axis order to X, Y, Z (1, 2, 3)
    '''
    # just reorders axis to X, Y, Z (https://gemmi.readthedocs.io/en/latest/grid.html#setup)
    map_object.setup(float('nan'), gemmi.MapSetup.ReorderOnly)
    ccp4_header = self.__read_ccp4_words_to_dict(map_object)
    new_axis_order = ccp4_header['MAPC'], ccp4_header['MAPR'], ccp4_header['MAPS']
    assert new_axis_order == (1, 2, 3), f'Axis order is {new_axis_order}, should be (1, 2, 3) or X, Y, Z'
    return map_object

def read_volume_map_to_object(self, volume_file_path: Path) -> gemmi.Ccp4Map:
    '''
    Reads ccp4 map to gemmi.Ccp4Map object
    '''
    # https://www.ccpem.ac.uk/mrc_format/mrc2014.php
    # https://www.ccp4.ac.uk/html/maplib.html
    return gemmi.read_ccp4_map(str(volume_file_path.resolve()))
