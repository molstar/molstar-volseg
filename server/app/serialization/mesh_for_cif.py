import numpy as np

from db.interface.i_preprocessed_db import MeshesData  # type: ignore


class MeshesForCif(object):
    mesh__id: np.ndarray  # int
    vertex__mesh_id: np.ndarray  # int
    vertex__vertex_id: np.ndarray  # int # probably unnecessary because it's equal to the vertex's index within the mesh
    vertex__x: np.ndarray  # float
    vertex__y: np.ndarray  # float
    vertex__z: np.ndarray  # float
    triangle__mesh_id: np.ndarray  # int
    triangle__vertex_id: np.ndarray  # int

    def __init__(self, meshes: MeshesData) -> None:
        total_vertices = sum(mesh["vertices"].shape[0] for mesh in meshes)
        total_triangles = sum(mesh["triangles"].shape[0] for mesh in meshes)

        if len(meshes) > 0:
            coord_type = meshes[0]["vertices"].dtype
            index_type = meshes[0]["triangles"].dtype
        else:
            coord_type = np.float32
            index_type = np.int32
        
        self.mesh__id = np.array([mesh["mesh_id"] for mesh in meshes], dtype=index_type)
        self.vertex__mesh_id = np.empty(shape=(total_vertices,), dtype=index_type)
        self.vertex__vertex_id = np.empty(shape=(total_vertices,), dtype=index_type)
        self.vertex__x = np.empty(shape=(total_vertices,), dtype=coord_type)
        self.vertex__y = np.empty(shape=(total_vertices,), dtype=coord_type)
        self.vertex__z = np.empty(shape=(total_vertices,), dtype=coord_type)
        self.triangle__mesh_id = np.empty(shape=(3*total_triangles), dtype=index_type)
        self.triangle__vertex_id = np.empty(shape=(3*total_triangles), dtype=index_type)
        
        vertex_offset = 0
        triangle_offset = 0
        for mesh in meshes:
            nv = mesh["vertices"].shape[0]
            self.vertex__mesh_id[vertex_offset:vertex_offset+nv] = mesh["mesh_id"]
            self.vertex__vertex_id[vertex_offset:vertex_offset+nv] = np.arange(nv)
            self.vertex__x[vertex_offset:vertex_offset+nv] = mesh["vertices"][:, 0]
            self.vertex__y[vertex_offset:vertex_offset+nv] = mesh["vertices"][:, 1]
            self.vertex__z[vertex_offset:vertex_offset+nv] = mesh["vertices"][:, 2]
            vertex_offset += nv

            nt = mesh["triangles"].shape[0]
            self.triangle__mesh_id[triangle_offset:triangle_offset+3*nt] = mesh["mesh_id"]
            self.triangle__vertex_id[triangle_offset:triangle_offset+3*nt] = mesh["triangles"].ravel()
            triangle_offset += 3*nt
    
    def n_meshes(self) -> int:
        return self.mesh__id.shape[0]

    def n_vertices(self) -> int:
        return self.vertex__mesh_id.shape[0]
    
    def n_triangles(self) -> int:
        return self.triangle__mesh_id.shape[0] // 3