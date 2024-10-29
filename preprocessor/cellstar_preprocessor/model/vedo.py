from cellstar_db.models import ModelArbitraryTypes, PreparedMeshData, VedoMeshData
import numpy as np
from pydantic.dataclasses import dataclass
from vedo import Mesh
import dask.array as da

class Config:
    arbitrary_types_allowed = True

@dataclass(config=Config)
class VedoMesh:
    # try dask, if not - np
    vertices: da.Array
    triangles: da.Array
    # mesh: Mesh | None = None
    
    def __post_init__(self):
        self.mesh = Mesh([self.vertices, self.triangles])
    
    def compute_vertex_density(self):
        """Takes as input mesh list group with stored original lvl meshes.
        Returns estimate of vertex_density for mesh list"""
        total_vertex_count = self.vertices.shape[0]
        total_area = self.mesh.area
        return total_vertex_count / total_area

    def simplify_mesh(self, 
        fraction: float,
        segment_id: int, mesh_id: int
    ):
        self.mesh = self.mesh.decimate(fraction=fraction)
        return self.__get_prepared_mesh_data(
            segment_id=segment_id, fraction=fraction, mesh_id=mesh_id
        )
    def __get_prepared_mesh_data(self, segment_id: int, fraction: float, mesh_id: int):
        return PreparedMeshData(
            vertices=da.from_array(self.mesh.vertices, dtype=np.float32),
            triangles=da.from_array(self.mesh.vertices, dtype=np.float32),
            normals=da.from_array(self.mesh.vertices, dtype=np.float32),
            area=self.mesh.area(),
            segment_id=segment_id,
            fraction=fraction,
            mesh_id=mesh_id
        )
        
