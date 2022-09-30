import numpy as np

from db.interface.i_preprocessed_db import MeshesData  # type: ignore

class WithArrays(object):
    def try_shrink_uint_array_attrs(self) -> None:
        '''Try to shrink dtype of all positive-integer ndarray attributes.'''
        for attr, value in vars(self).items():
            if isinstance(value, np.ndarray):
                shrinked = self.try_shrink_uint_array(value)
                self.__setattr__(attr, shrinked)

    @staticmethod
    def try_shrink_uint_array(array: np.ndarray):
        '''Try to cast `array` into a smallest sufficient uint dtype. 
        If cannot shrink anymore, return the original array.
        If `array` is not of integer (int or uint) dtype or contains negative values, return the original array.'''
        if array.dtype.kind not in 'iu':  # check if int or uint
            return array
        if array.size == 0:
            return array
        current_itemsize: int = array.dtype.itemsize  # in bytes
        minimum = array.min()
        maximum = array.max()
        if minimum < 0:
            return array
        # print('try_shrink_uint_dtype', minimum, maximum, array.dtype, current_itemsize)
        for dtype_class in (np.uint8, np.uint16, np.uint32, np.uint64):
            itemsize: int = np.dtype(dtype_class).itemsize
            limit = 2**(8*itemsize) - 1
            # print(dtype_class, '?', limit)
            if maximum <= limit:
                if itemsize < current_itemsize:
                    # print('yep, convert to', dtype_class)
                    return array.astype(dtype_class)
                else:
                    # print('yep, keep', array.dtype)
                    return array
        # print('nope')
        return array


class MeshesForCif(WithArrays):
    '''Representation of meshes prepared for conversion to binary CIF.'''
    mesh__id: np.ndarray  # int
    vertex__mesh_id: np.ndarray  # int
    vertex__vertex_id: np.ndarray  # probably unnecessary because it's equal to the vertex's index within the mesh
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
            index_type = np.uint32
        
        self.mesh__id = np.array([mesh["mesh_id"] for mesh in meshes], dtype=index_type)
        self.vertex__mesh_id = np.empty((total_vertices,), dtype=index_type)
        self.vertex__vertex_id = np.empty((total_vertices,), dtype=index_type)
        self.vertex__x = np.empty((total_vertices,), dtype=coord_type)
        self.vertex__y = np.empty((total_vertices,), dtype=coord_type)
        self.vertex__z = np.empty((total_vertices,), dtype=coord_type)
        self.triangle__mesh_id = np.empty((3*total_triangles), dtype=index_type)
        self.triangle__vertex_id = np.empty((3*total_triangles), dtype=index_type)
        
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

        self.try_shrink_uint_array_attrs()
        return
