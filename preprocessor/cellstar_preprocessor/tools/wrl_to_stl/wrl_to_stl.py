from pathlib import Path
from cellstar_preprocessor.tools.convert_app_specific_segm_to_sff.convert_app_specific_segm_to_sff import convert_app_specific_segm_to_sff
import pymeshlab


def wrl_to_stl(input: Path, output: Path):
    ms = pymeshlab.MeshSet()
    ms.load_new_mesh(str(input.resolve()))
    ms.save_current_mesh(str(output.resolve()))
    return output