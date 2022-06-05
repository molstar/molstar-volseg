from pathlib import Path
from vedo import Mesh, show
from preprocessor.src.preprocessors.implementations.sff.preprocessor.constants import SEGMENTATION_DATA_GROUPNAME

from preprocessor.src.preprocessors.implementations.sff.preprocessor.sff_preprocessor import open_zarr_structure_from_path
MESH_SEGM_PATH = Path('db/empiar/empiar-10070')
mesh_entry_root = open_zarr_structure_from_path(MESH_SEGM_PATH)
_mesh_segmentation_data = mesh_entry_root[SEGMENTATION_DATA_GROUPNAME]

faces = _mesh_segmentation_data[1][17][0].triangles[...]
verts = _mesh_segmentation_data[1][17][0].vertices[...]

# Build the polygonal Mesh object:
mesh = Mesh([verts, faces])
show(mesh)
new_mesh = mesh.decimate(fraction=0.1)
show(new_mesh)
a = 0