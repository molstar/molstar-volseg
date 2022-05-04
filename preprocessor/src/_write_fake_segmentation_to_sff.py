from pathlib import Path
from typing import List
import sfftkrw as sff
import numpy as np
import random
import string

from preprocessor.src._create_fake_segmentation_from_real_volume import create_fake_segmentation_from_real_volume

# TODO: change to big EMDB entry name once ready
OUTPUT_FILEPATH = Path('preprocessor/fake_segmentations/fake_emd_1832.hff')
# Just for testing
# FILEPATH_JSON = Path('preprocessor/fake_segmentations/fake_emd_1832.json')

REAL_MAP_FILEPATH = Path('preprocessor\sample_volumes\emdb_sff\EMD-1832.map')

def write_fake_segmentation_to_sff(output_filepath: Path, lattice_data: np.ndarray, segm_ids: List[int], json_for_debug=False):
    '''
    Note: creates a single lattice
    '''
    # based on filepath name
    seg_name = (output_filepath.stem).lower()
    seg_details = seg_name

    seg = sff.SFFSegmentation(name=seg_name, primary_descriptor="three_d_volume")
    seg.details = seg_details
    # TODO:
    # we need:
    # sfftkrw.SFFSegmentList - for segment items we need to have ids
    # sfftkrw.SFFLatticeList
    # and their itmes
    # the algorithm of creating those two:
    # 1. Instantiate container (*List)
    # 2. Instantiate all items with ids
    # provide ids upon instantiation:
    # seg1 = sff.SFFSegment(id=37)
    # generate colors randomly
    seg.lattice_list = sff.SFFLatticeList()

    cols, rows, sections = lattice_data.shape
    _size = sff.SFFVolumeStructure(cols=cols, rows=rows, sections=sections)
    _start = sff.SFFVolumeIndex(cols=0, rows=0, sections=0)

    lattice_obj = sff.SFFLattice.from_array(
        data=lattice_data,
        mode='uint32',
        endianness='little',
        size=_size,
        start=_start,
    )
    lattice_obj.id = 0
    seg.lattice_list.append(lattice_obj)

    seg.segment_list = sff.SFFSegmentList()
    for segment_id in segm_ids:
        segment = _instantiate_segment(segment_id, value=segment_id)
        seg.segment_list.append(segment)

    try:
        seg.to_file(str(output_filepath.resolve()))
        # probably sfftk bug: module 'os' has no attribute 'EX_OK'
    except AttributeError:
        pass

    if json_for_debug == True:
        try:
            output_json_filepath = output_filepath.with_suffix('.json')
            seg.to_file(str(output_json_filepath.resolve()))
        except AttributeError:
            pass


def _instantiate_segment(segm_id: int, value, lattice_id=0):
    segment = sff.SFFSegment(id=segm_id)
    segment.three_d_volume = sff.SFFThreeDVolume(
        lattice_id=lattice_id,
        value=value,
    )
    segment.colour = sff.SFFRGBA(
        red=random.random(),
        green=random.random(),
        blue=random.random(),
        alpha=random.random()
    )
    
    random_name = ''.join(random.choices(string.ascii_lowercase, k=15))
    random_descr = ''.join(random.choices(string.ascii_lowercase, k=30))
    segment.biological_annotation = sff.SFFBiologicalAnnotation(
        name=random_name,
        description=random_descr
    )
    return segment


if __name__ == '__main__':
    segm_grid_and_ids = create_fake_segmentation_from_real_volume(REAL_MAP_FILEPATH, 10)
    grid = segm_grid_and_ids['grid']
    segm_ids = segm_grid_and_ids['ids']
    write_fake_segmentation_to_sff(
        OUTPUT_FILEPATH,
        lattice_data=grid,
        segm_ids=segm_ids,
        json_for_debug=True
        )