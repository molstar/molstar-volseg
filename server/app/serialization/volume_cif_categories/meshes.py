'''CIF categories for mesh encoding (_mesh, _mesh_vertex, _mesh_triangle)'''

from ciftools.writer.base import FieldDesc  # type: ignore
from ciftools.writer.fields import number_field  # type: ignore

from app.serialization.volume_cif_categories.common import CategoryWriterProviderBase
from app.serialization.volume_cif_categories import encoders
from app.serialization.meshes_for_cif import MeshesForCif


class CategoryWriterProvider_Mesh(CategoryWriterProviderBase[MeshesForCif]):
    category_name = 'mesh'

    def get_row_count(self, data: MeshesForCif) -> int:
        return data.mesh__id.shape[0]

    def get_field_descriptors(self, data: MeshesForCif) -> list[FieldDesc]:
        def get_id(meshes: MeshesForCif, i: int) -> int:
            return meshes.mesh__id[i]  

        return [
            number_field(name="id", value=get_id, dtype=data.mesh__id.dtype, encoder=encoders.bytearray_encoder),  # usually only 1 row
        ]


class CategoryWriterProvider_MeshVertex(CategoryWriterProviderBase[MeshesForCif]):
    category_name = 'mesh_vertex'

    def get_row_count(self, data: MeshesForCif) -> int:
        return data.vertex__mesh_id.shape[0]

    def get_field_descriptors(self, data: MeshesForCif) -> list[FieldDesc]:
        def get_mesh_id(meshes: MeshesForCif, i: int) -> int:
            return meshes.vertex__mesh_id[i]
        def get_vertex_id(meshes: MeshesForCif, i: int) -> int:
            return meshes.vertex__vertex_id[i]
        def get_x(meshes: MeshesForCif, i: int) -> float:
            return meshes.vertex__x[i]
        def get_y(meshes: MeshesForCif, i: int) -> float:
            return meshes.vertex__y[i]
        def get_z(meshes: MeshesForCif, i: int) -> float:
            return meshes.vertex__z[i]
        # This is actually inefficient as hell. 
        # Here we select individual values from an array, 
        # which are then put back together into an array in ciftools.

        def x_encoder(meshes: MeshesForCif):
            return encoders.coord_encoder(meshes.vertex__x)
        def y_encoder(meshes: MeshesForCif):
            return encoders.coord_encoder(meshes.vertex__y)
        def z_encoder(meshes: MeshesForCif):
            return encoders.coord_encoder(meshes.vertex__z)

        return [
            number_field(name="mesh_id", value=get_mesh_id, dtype=data.vertex__mesh_id.dtype, encoder=encoders.delta_rl_encoder),
            number_field(name="vertex_id", value=get_vertex_id, dtype=data.vertex__vertex_id.dtype, encoder=encoders.delta_rl_encoder),
            number_field(name="x", value=get_x, dtype=data.vertex__x.dtype, encoder=x_encoder),
            number_field(name="y", value=get_y, dtype=data.vertex__y.dtype, encoder=y_encoder),
            number_field(name="z", value=get_z, dtype=data.vertex__z.dtype, encoder=z_encoder),
        ]


class CategoryWriterProvider_MeshTriangle(CategoryWriterProviderBase[MeshesForCif]):
    category_name = 'mesh_triangle'

    def get_row_count(self, data: MeshesForCif) -> int:
        return data.triangle__mesh_id.shape[0]

    def get_field_descriptors(self, data: MeshesForCif) -> list[FieldDesc]:
        def get_mesh_id(meshes: MeshesForCif, i: int) -> int:
            return meshes.triangle__mesh_id[i]
        def get_vertex_id(meshes: MeshesForCif, i: int) -> int:
            return meshes.triangle__vertex_id[i]

        return [
            number_field(name="mesh_id", value=get_mesh_id, dtype=data.triangle__mesh_id.dtype, encoder=encoders.delta_rl_encoder),
            number_field(name="vertex_id", value=get_vertex_id, dtype=data.triangle__vertex_id.dtype, encoder=encoders.bytearray_encoder),  # delta_intpack_encoder is a bit better but slow
        ]
