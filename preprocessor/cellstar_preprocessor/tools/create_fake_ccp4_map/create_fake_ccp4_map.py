from pathlib import Path

import gemmi
import numpy as np


def create_fake_ccp4_map(
    grid_size: tuple[int, int, int], filepath: Path, dtype, axis_order: tuple
):
    ccp4 = gemmi.Ccp4Map()
    # ccp4.grid = gemmi.FloatGrid(np.random.rand(*grid_size).astype(dtype=dtype))
    ccp4.grid = gemmi.FloatGrid(np.ones(grid_size).astype(dtype=dtype))

    # TODO: these two is relevant?
    ccp4.grid.unit_cell.set(20, 20, 20, 90, 90, 90)
    ccp4.grid.spacegroup = gemmi.SpaceGroup("P1")

    ccp4.update_ccp4_header()
    ccp4.set_header_i32(17, axis_order[0] + 1)
    ccp4.set_header_i32(18, axis_order[1] + 1)
    ccp4.set_header_i32(19, axis_order[2] + 1)

    ccp4.update_ccp4_header()
    filepath.parent.mkdir(parents=True, exist_ok=True)
    ccp4.write_ccp4_map(str(filepath.resolve()))


if __name__ == "__main__":
    grid_size = (4, 3, 2)
    map_filepath = Path(f"preprocessor/temp/fake_ccp4_ZYX.map")
    create_fake_ccp4_map(
        grid_size=grid_size,
        filepath=map_filepath,
        dtype=np.float32,
        axis_order=(2, 1, 0),
    )
