
from pathlib import Path
from cellstar_preprocessor.flows.segmentation.helper_methods import open_hdf5_as_segmentation_object
from cellstar_preprocessor.tools.convert_app_specific_segm_to_sff.convert_app_specific_segm_to_sff import convert_app_specific_segm_to_sff
import pymeshlab


def convert_wrl_to_sff(input_file: Path, working_folder: Path):
    ms = pymeshlab.MeshSet()
# You can load, save meshes and apply MeshLab filters:
    stl_path = working_folder / 'temp_stl_dir' / 'temp_stl.stl'
    ms.load_new_mesh(str(input_file.resolve()))
    ms.save_current_mesh(str(stl_path.resolve()))
    sff_path = convert_app_specific_segm_to_sff(stl_path)
    # sff_obj = open_hdf5_as_segmentation_object(sff)
    return sff_path