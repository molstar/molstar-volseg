from pathlib import Path
import gemmi
import numpy as np


def create_fake_ccp4_map(grid_size: tuple[int, int, int], filepath: Path):
    ccp4 = gemmi.Ccp4Map()
    ccp4.grid = gemmi.FloatGrid(np.zeros(grid_size, dtype=np.float32))

    # TODO: these two is relevant?
    ccp4.grid.unit_cell.set(20, 20, 20, 90, 90, 90)
    ccp4.grid.spacegroup = gemmi.SpaceGroup('P1')
    
    ccp4.update_ccp4_header()
    ccp4.write_ccp4_map(filepath)