from pathlib import Path
import sfftkrw as sff
import numpy as np

from preprocessor._create_fake_segmentation_from_real_volume import create_fake_segmentation_from_real_volume

# TODO: once the core parts of SFF (lattice & some other things) are ready, add some fake annotations
# don't bother with software list etc. Just some random strings of text
def write_fake_segmentation_to_sff(output_filepath: Path, lattice_data: np.ndarray, OTHER_ARGS_TODO=None):
    seg = sff.SFFSegmentation(name="my segmentation", primary_descriptor="three_d_volume")
    seg.to_file(str(output_filepath.resolve()))

    # TODO: read docs and check fields
    # https://sfftk-rw.readthedocs.io/en/latest/developing.html
    seg.lattice_list = sff.SFFLatticeList()
    lattice_obj = sff.SFFLattice.from_array(lattice_data,
        mode='uint8',
        endianness='little',
        size=sff.SFFVolumeStructure(cols=10, rows=10, sections=10),
        start=sff.SFFVolumeIndex(cols=0, rows=0, sections=0),
    )
    # append to lat list etc.

if __name__ == '__main__':
    # TODO: change to big EMDB entry name once ready
    OUTPUT_FILEPATH = Path('preprocessor\fake_segmentations\fake_emd_1832.hff')
    REAL_MAP_FILEPATH = Path('preprocessor\sample_volumes\emdb_sff\EMD-1832.map')

    segm_grid = create_fake_segmentation_from_real_volume(REAL_MAP_FILEPATH, 10)
    write_fake_segmentation_to_sff(
        OUTPUT_FILEPATH,
        lattice_data=segm_grid
        )
