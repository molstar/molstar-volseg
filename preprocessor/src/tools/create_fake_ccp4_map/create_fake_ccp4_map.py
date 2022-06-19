from pathlib import Path
import gemmi
from matplotlib.pyplot import grid
import numpy as np

from preprocessor.src.preprocessors.implementations.sff.preprocessor._volume_map_methods import read_and_normalize_map


def create_fake_ccp4_map(grid_size: tuple[int, int, int], filepath: Path):
    ccp4 = gemmi.Ccp4Map()
    ccp4.grid = gemmi.FloatGrid(np.zeros(grid_size, dtype=np.float32))

    # TODO: these two is relevant?
    ccp4.grid.unit_cell.set(20, 20, 20, 90, 90, 90)
    ccp4.grid.spacegroup = gemmi.SpaceGroup('P1')
    
    ccp4.update_ccp4_header()
    filepath.parent.mkdir(parents=True, exist_ok=True)
    ccp4.write_ccp4_map(str(filepath.resolve()))



if __name__ == '__main__':
    large_map_filepath = Path('preprocessor/data/raw_input_files/emdb/emd-88888/fake_large_map.ccp4')
    grid_size = (1000, 1000, 1000)
    create_fake_ccp4_map(grid_size=grid_size, filepath=large_map_filepath)

    arr = read_and_normalize_map(large_map_filepath)

    print(arr.shape)