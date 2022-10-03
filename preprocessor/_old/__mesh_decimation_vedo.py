from pathlib import Path
from vedo import Mesh, show
from db.file_system.constants import SEGMENTATION_DATA_GROUPNAME
from preprocessor.src.preprocessors.implementations.sff.preprocessor.downsampling.downsampling import compute_vertex_density

from preprocessor.src.preprocessors.implementations.sff.preprocessor.sff_preprocessor import open_zarr_structure_from_path
MESH_SEGM_PATH = Path('db/empiar/empiar-10070')
mesh_entry_root = open_zarr_structure_from_path(MESH_SEGM_PATH)
_mesh_segmentation_data = mesh_entry_root[SEGMENTATION_DATA_GROUPNAME]



faces = _mesh_segmentation_data[16][1][0].triangles[...]
verts = _mesh_segmentation_data[16][1][0].vertices[...]

# Build the polygonal Mesh object:
mesh = Mesh([verts, faces])
# show(mesh)
print(len(mesh.points()))
print(len(mesh.faces()))
new_mesh = mesh.decimate(fraction=0.1)
# show(new_mesh)
print(len(new_mesh.points()))
print(len(new_mesh.faces()))

sample_mesh_list_gr_1 = _mesh_segmentation_data[16][1]
sample_mesh_list_gr_2 = _mesh_segmentation_data[17][1]

vertex_density_1_area = compute_vertex_density(sample_mesh_list_gr_1, mode='area')
# vertex_density_1_volume = compute_vertex_density(sample_mesh_list_gr_1, mode='volume')

vertex_density_2_area = compute_vertex_density(sample_mesh_list_gr_2, mode='area')
# vertex_density_2_volume = compute_vertex_density(sample_mesh_list_gr_2, mode='volume')

print(f'mesh 1 list vertex density, area: {vertex_density_1_area}')
# print(f'mesh 1 list vertex density,  volume: {vertex_density_1_volume}')

print(f'mesh 2 list vertex density, area: {vertex_density_2_area}')
# print(f'mesh 2 list vertex density,  volume: {vertex_density_2_volume}')


a = 0