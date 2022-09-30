import numpy as np
from ciftools.binary.encoding.base.cif_encoder_base import CIFEncoderBase
from ciftools.binary.encoding.data_types import DataType, DataTypeEnum
from ciftools.binary.encoding.impl.binary_cif_encoder import BinaryCIFEncoder
from ciftools.binary.encoding.impl.encoders.byte_array import ByteArrayCIFEncoder
from ciftools.writer.base import CategoryWriter, CategoryWriterProvider, FieldDesc
from ciftools.writer.fields import number_field

from db.interface.i_preprocessed_db import MeshesData

from app.serialization.volume_cif_categories.common import CategoryDesc, CategoryDescImpl
from app.serialization.volume_cif_categories.category_writer_base import CategoryWriterBase
from app.serialization.mesh_for_cif import MeshesForCif


INT_32 = DataType.to_dtype(DataTypeEnum.Int32)


class CategoryWriterProvider_MeshVertex(CategoryWriterProvider):
    def category_writer(self, ctx: MeshesForCif) -> CategoryWriter:
        field_desc: list[FieldDesc] = Fields_MeshVertex().fields
        return CategoryWriterBase(ctx, ctx.vertex__mesh_id.shape[0], CategoryDescImpl("mesh_vertex", field_desc))


class Fields_MeshVertex(object):
    def __init__(self):
        def make_byte_array_encoder(_) -> BinaryCIFEncoder:
            return BinaryCIFEncoder([ByteArrayCIFEncoder()])

        def get_id(meshes: MeshesForCif, i: int) -> int:
            return meshes.mesh__id[i]  
            # This is actually inefficient as hell. 
            # Here we select individual values from an array, 
            # which are then put back together into an array in ciftools.

        self.fields: list[FieldDesc] = [
            number_field(name="id", value=get_id, dtype=INT_32, encoder=make_byte_array_encoder),  # TODO run-length of delta?
        ]
