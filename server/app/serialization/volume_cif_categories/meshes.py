'''CIF categories for mesh encoding (_mesh, _mesh_vertex, _mesh_triangle)'''

from ciftools.writer.base import FieldDesc
from ciftools.writer.fields import number_field, FieldArrays

from app.serialization.volume_cif_categories.common import CategoryWriterProviderBase
from app.serialization.volume_cif_categories import encoders
from app.serialization.meshes_for_cif import MeshesForCif

class CategoryWriterProvider_Mesh(CategoryWriterProviderBase[MeshesForCif]):
    category_name = 'mesh'

    def get_row_count(self, data: MeshesForCif) -> int:
        return data.mesh__id.shape[0]

    def get_field_descriptors(self, data: MeshesForCif) -> list[FieldDesc]:

        return [
            number_field(name="id", arrays=lambda d: FieldArrays(d.mesh__id), dtype=data.mesh__id.dtype, encoder=encoders.bytearray_encoder),  # usually only 1 row
        ]


class CategoryWriterProvider_MeshVertex(CategoryWriterProviderBase[MeshesForCif]):
    category_name = 'mesh_vertex'

    def get_row_count(self, data: MeshesForCif) -> int:
        return data.vertex__mesh_id.shape[0]

    def get_field_descriptors(self, data: MeshesForCif) -> list[FieldDesc]:
        def x_encoder(meshes: MeshesForCif):
            return encoders.coord_encoder(meshes.vertex__x)
        def y_encoder(meshes: MeshesForCif):
            return encoders.coord_encoder(meshes.vertex__y)
        def z_encoder(meshes: MeshesForCif):
            return encoders.coord_encoder(meshes.vertex__z)

        return [
            number_field(name="mesh_id", arrays=lambda d: FieldArrays(d.vertex__mesh_id), dtype=data.vertex__mesh_id.dtype, encoder=encoders.delta_rl_encoder),
            number_field(name="vertex_id", arrays=lambda d: FieldArrays(d.vertex__vertex_id), dtype=data.vertex__vertex_id.dtype, encoder=encoders.delta_rl_encoder),
            number_field(name="x", arrays=lambda d: FieldArrays(d.vertex__x), dtype=data.vertex__x.dtype, encoder=x_encoder),
            number_field(name="y", arrays=lambda d: FieldArrays(d.vertex__y), dtype=data.vertex__y.dtype, encoder=y_encoder),
            number_field(name="z", arrays=lambda d: FieldArrays(d.vertex__z), dtype=data.vertex__z.dtype, encoder=z_encoder),
        ]


class CategoryWriterProvider_MeshTriangle(CategoryWriterProviderBase[MeshesForCif]):
    category_name = 'mesh_triangle'

    def get_row_count(self, data: MeshesForCif) -> int:
        return data.triangle__mesh_id.shape[0]

    def get_field_descriptors(self, data: MeshesForCif) -> list[FieldDesc]:

        return [
            number_field(name="mesh_id", arrays=lambda d: FieldArrays(d.triangle__mesh_id), dtype=data.triangle__mesh_id.dtype, encoder=encoders.delta_rl_encoder),
            number_field(name="vertex_id", arrays=lambda d: FieldArrays(d.triangle__vertex_id), dtype=data.triangle__vertex_id.dtype, encoder=encoders.bytearray_encoder),  # delta_intpack_encoder is a bit better but slow
        ]
