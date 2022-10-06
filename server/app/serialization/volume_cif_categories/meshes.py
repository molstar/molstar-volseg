"""CIF categories for mesh encoding (_mesh, _mesh_vertex, _mesh_triangle)"""

from ciftools.models.writer import CIFCategoryDesc
from ciftools.models.writer import CIFFieldDesc as Field

from app.serialization.data.meshes_for_cif import MeshesForCif
from app.serialization.volume_cif_categories import encoders


class CategoryWriterProvider_Mesh(CIFCategoryDesc):
    name = "mesh"

    @staticmethod
    def get_row_count(data: MeshesForCif) -> int:
        return data.mesh__id.shape[0]

    @staticmethod
    def get_field_descriptors(data: MeshesForCif):
        return [
            Field[MeshesForCif].number_array(
                name="id", array=lambda d: d.mesh__id, dtype=data.mesh__id.dtype, encoder=encoders.bytearray_encoder
            ),  # usually only 1 row
        ]


class CategoryWriterProvider_MeshVertex(CIFCategoryDesc):
    name = "mesh_vertex"

    @staticmethod
    def get_row_count(data: MeshesForCif) -> int:
        return data.vertex__mesh_id.shape[0]

    @staticmethod
    def get_field_descriptors(data: MeshesForCif):
        def x_encoder(meshes: MeshesForCif):
            return encoders.coord_encoder(meshes.vertex__x)

        def y_encoder(meshes: MeshesForCif):
            return encoders.coord_encoder(meshes.vertex__y)

        def z_encoder(meshes: MeshesForCif):
            return encoders.coord_encoder(meshes.vertex__z)

        return [
            Field[MeshesForCif].number_array(
                name="mesh_id",
                array=lambda d: d.vertex__mesh_id,
                dtype=data.vertex__mesh_id.dtype,
                encoder=encoders.delta_rl_encoder,
            ),
            Field[MeshesForCif].number_array(
                name="vertex_id",
                array=lambda d: d.vertex__vertex_id,
                dtype=data.vertex__vertex_id.dtype,
                encoder=encoders.delta_rl_encoder,
            ),
            Field[MeshesForCif].number_array(
                name="x", array=lambda d: d.vertex__x, dtype=data.vertex__x.dtype, encoder=x_encoder
            ),
            Field[MeshesForCif].number_array(
                name="y", array=lambda d: d.vertex__y, dtype=data.vertex__y.dtype, encoder=y_encoder
            ),
            Field[MeshesForCif].number_array(
                name="z", array=lambda d: d.vertex__z, dtype=data.vertex__z.dtype, encoder=z_encoder
            ),
        ]


class CategoryWriterProvider_MeshTriangle(CIFCategoryDesc):
    name = "mesh_triangle"

    @staticmethod
    def get_row_count(data: MeshesForCif) -> int:
        return data.triangle__mesh_id.shape[0]

    @staticmethod
    def get_field_descriptors(data: MeshesForCif):
        return [
            Field[MeshesForCif].number_array(
                name="mesh_id",
                array=lambda d: d.triangle__mesh_id,
                dtype=data.triangle__mesh_id.dtype,
                encoder=encoders.delta_rl_encoder,
            ),
            Field[MeshesForCif].number_array(
                name="vertex_id",
                array=lambda d: d.triangle__vertex_id,
                dtype=data.triangle__vertex_id.dtype,
                encoder=encoders.bytearray_encoder,
            ),  # delta_intpack_encoder is a bit better but slow
        ]
