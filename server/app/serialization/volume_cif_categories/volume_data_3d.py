import numpy as np

from ciftools.writer.base import FieldDesc
from ciftools.writer.fields import number_field, FieldArrays

from app.serialization.volume_cif_categories.common import CategoryWriterProviderBase
from app.serialization.volume_cif_categories import encoders


class CategoryWriterProvider_VolumeData3d(CategoryWriterProviderBase[np.ndarray]):
    category_name = 'volume_data_3d'

    def get_row_count(self, ctx: np.ndarray) -> int:
        return ctx.size

    def get_field_descriptors(self, ctx: np.ndarray) -> list[FieldDesc]:
        encoder, dtype = encoders.decide_encoder(ctx, 'VolumeData3d')
        return [
            number_field(name="values", arrays=lambda volume: FieldArrays(volume), encoder=lambda d: encoder, dtype=dtype),
        ]
