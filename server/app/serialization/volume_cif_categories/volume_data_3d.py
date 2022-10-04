import numpy as np
from ciftools.models.writer import CIFCategoryDesc
from ciftools.models.writer import CIFFieldDesc as Field

from app.serialization.volume_cif_categories import encoders


class VolumeData3dCategory(CIFCategoryDesc):
    name = "volume_data_3d"

    @staticmethod
    def get_row_count(ctx: np.ndarray) -> int:
        return ctx.size

    @staticmethod
    def get_field_descriptors(ctx: np.ndarray):
        encoder, dtype = encoders.decide_encoder(ctx, "VolumeData3d")
        return [
            Field.number_array(name="values", array=lambda volume: volume, encoder=lambda _: encoder, dtype=dtype),
        ]
