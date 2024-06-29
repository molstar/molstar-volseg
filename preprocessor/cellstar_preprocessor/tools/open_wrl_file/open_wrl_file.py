
from pathlib import Path
from cellstar_preprocessor.flows.segmentation.helper_methods import open_hdf5_as_segmentation_object
from cellstar_preprocessor.tools.convert_app_specific_segm_to_sff.convert_app_specific_segm_to_sff import convert_app_specific_segm_to_sff
import pymeshlab


if __name__ == '__main__':
    WRL_FILE = 'preprocessor/cellstar_preprocessor/tools/open_wrl_file/actin.wrl'
    STL_FILE = 'preprocessor/cellstar_preprocessor/tools/open_wrl_file/actin.stl'
    ms = pymeshlab.MeshSet()
# You can load, save meshes and apply MeshLab filters:
    wrl_path = Path(WRL_FILE)
    stl_path = Path(STL_FILE)
    ms.load_new_mesh(str(wrl_path.resolve()))
    print()
    ms.save_current_mesh(str(stl_path.resolve()))
    print()
    
    sff = convert_app_specific_segm_to_sff(stl_path)
    sff_obj = open_hdf5_as_segmentation_object(sff)
    print(sff_obj)
    # ms.generate_convex_hull()
    # ms.save_current_mesh('convex_hull.ply')