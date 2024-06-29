
from pathlib import Path
import pymeshlab


if __name__ == '__main__':
    WRL_FILE = str(Path('preprocessor/cellstar_preprocessor/tools/open_wrl_file/actin.wrl').resolve())
    STL_FILE = str(Path('preprocessor/cellstar_preprocessor/tools/open_wrl_file/actin.stl').resolve())
    ms = pymeshlab.MeshSet()
# You can load, save meshes and apply MeshLab filters:

    ms.load_new_mesh(WRL_FILE)
    print()
    ms.save_current_mesh(STL_FILE)
    print()
    # ms.generate_convex_hull()
    # ms.save_current_mesh('convex_hull.ply')