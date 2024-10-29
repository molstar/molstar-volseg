from pathlib import Path
import re
import subprocess
from cellstar_preprocessor.tools.convert_app_specific_segm_to_sff.convert_app_specific_segm_to_sff import convert_app_specific_segm_to_sff
import numpy as np
import pymeshlab

# NOTE: loads way too long
def wrl_to_stl(input: Path, output: Path):
    ms = pymeshlab.MeshSet()
    ms.load_new_mesh(str(input.resolve()))
    ms.save_current_mesh(str(output.resolve()))
    return output



# import trimesh

# NOTE: produces small mesh
# def wrl_to_stl(input_path: Path, output_path: Path):
#     with open(str(input_path.resolve()), 'r', encoding='utf8') as f:
#         s = f.read()

#         s2 = re.sub(r'\n|\r|,', ' ', s)
#         s3 = re.sub('\s+', ' ', s2)
        
#         l1 = re.search(r'point \[(.*?)\]', s3).group(1).strip().split()
#         points = np.float32(l1).reshape((-1,3))

        
#         # TODO: dask?
#         l2 = re.search(r'coordIndex \[(.*?)\]', s3).group(1).strip().split()
#         coordIndexs = np.int32(l2).reshape((-1,4))

#         mesh = trimesh.Trimesh(vertices=points, faces=coordIndexs[:,:3])
#         mesh.export(str(output_path.resolve()))
#         return output_path


# NOTE: small mesh + drawback - CLI program
# def wrl_to_stl(i: Path, o: Path):
#     s = f"./meshconv {str(i.resolve())} -c stl"
#     lst = s.split(" ")
#     p = subprocess.Popen(lst)
#     return o

PATH_TO_CONVERTER = Path('external_tools/castle_model_converter/castle-model-converter')


# # NOTE: castle converter 
# def wrl_to_stl(i: Path, o: Path):
#     exe = str(PATH_TO_CONVERTER.resolve())
#     s = f"{exe} {str(i.resolve())} {str(o.resolve())}"
#     lst = s.split(" ")
#     p = subprocess.Popen(lst)
#     # not able to convert?
#     return o

# import wrlparser
# def wrl_to_stl(i: Path, o: Path):
#     with open(str(i.resolve())) as f:
#         l = "".join(f.readlines())
#         f.close()
        
#     scene = wrlparser.parse(l)
#     print(scene)