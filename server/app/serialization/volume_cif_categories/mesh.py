import numpy as np
from ciftools.binary.encoding.base.cif_encoder_base import CIFEncoderBase  # type: ignore
from ciftools.binary.encoding.impl.binary_cif_encoder import BinaryCIFEncoder  # type: ignore
from ciftools.binary.encoding.impl.encoders.byte_array import ByteArrayCIFEncoder  # type: ignore
from ciftools.writer.base import CategoryWriter, CategoryWriterProvider, FieldDesc  # type: ignore
from ciftools.writer.fields import number_field  # type: ignore

from . import category_writer_base as base
from app.serialization.mesh_for_cif import MeshesForCif  # type: ignore


class CategoryWriterProvider_Mesh(base.CategoryWriterProviderBase[MeshesForCif]):
    category_name = 'mesh'

    def get_row_count(self, data: MeshesForCif) -> int:
        return data.mesh__id.shape[0]

    def get_field_desc(self, data: MeshesForCif) -> list[FieldDesc]:
        def get_id(meshes: MeshesForCif, i: int) -> int:
            return meshes.mesh__id[i]  

        return [
            number_field(name="id", value=get_id, dtype=base.UINT_32, encoder=base.byte_array_encoder),  # TODO run-length of delta?
        ]


class CategoryWriterProvider_MeshVertex(base.CategoryWriterProviderBase[MeshesForCif]):
    category_name = 'mesh_vertex'

    def get_row_count(self, data: MeshesForCif) -> int:
        return data.vertex__mesh_id.shape[0]

    def get_field_desc(self, data: MeshesForCif) -> list[FieldDesc]:
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

        return [
            number_field(name="mesh_id", value=get_mesh_id, dtype=base.UINT_32, encoder=base.byte_array_encoder),  # TODO run-length of delta?
            number_field(name="vertex_id", value=get_vertex_id, dtype=base.UINT_32, encoder=base.byte_array_encoder),  # TODO run-length of delta?
            number_field(name="x", value=get_x, dtype=base.FLOAT_32, encoder=base.byte_array_encoder),
            number_field(name="y", value=get_y, dtype=base.FLOAT_32, encoder=base.byte_array_encoder),
            number_field(name="z", value=get_z, dtype=base.FLOAT_32, encoder=base.byte_array_encoder),
        ]


class CategoryWriterProvider_MeshTriangle(base.CategoryWriterProviderBase[MeshesForCif]):
    category_name = 'mesh_triangle'

    def get_row_count(self, data: MeshesForCif) -> int:
        return data.triangle__mesh_id.shape[0]

    def get_field_desc(self, data: MeshesForCif) -> list[FieldDesc]:
        def get_mesh_id(meshes: MeshesForCif, i: int) -> int:
            return meshes.triangle__mesh_id[i]
        def get_vertex_id(meshes: MeshesForCif, i: int) -> int:
            return meshes.triangle__vertex_id[i]

        return [
            number_field(name="mesh_id", value=get_mesh_id, dtype=base.UINT_32, encoder=base.byte_array_encoder),  # TODO run-length of delta?
            number_field(name="vertex_id", value=get_vertex_id, dtype=base.UINT_32, encoder=base.byte_array_encoder),  # TODO run-length of delta?
        ]
