import numpy as np
from ciftools.binary.encoding.impl.binary_cif_encoder import BinaryCIFEncoder
from ciftools.binary.encoding.data_types import DataType, DataTypeEnum
from ciftools.binary.encoding.base.cif_encoder_base import CIFEncoderBase
from ciftools.binary.encoding.impl.encoders.byte_array import ByteArrayCIFEncoder
from ciftools.writer.base import CategoryWriter, CategoryWriterProvider, FieldDesc

from app.serialization.volume_cif_categories.common import CategoryDesc, CategoryDescImpl, VolumeInfo


from typing import Callable, Optional, Union

import numpy as np
from ciftools.binary.encoding.impl.binary_cif_encoder import BinaryCIFEncoder
from ciftools.cif_format.value_presence import ValuePresenceEnum
from ciftools.writer.base import FieldDesc
from ciftools.writer.fields import number_field, string_field

from ciftools.binary.encoding.impl.encoders.byte_array import BYTE_ARRAY_CIF_ENCODER


class CategoryWriter_VolumeData3dInfo(CategoryWriter):
    def __init__(self, ctx: VolumeInfo, count: int, category_desc: CategoryDesc):
        self.data = ctx
        self.count = count
        self.desc = category_desc


class CategoryWriterProvider_VolumeData3dInfo(CategoryWriterProvider):
    def _decide_encoder(self, ctx: VolumeInfo) -> tuple[BinaryCIFEncoder, np.dtype]:
        pass

    def category_writer(self, ctx: VolumeInfo) -> CategoryWriter:
        field_desc: list[FieldDesc] = Fields_VolumeData3dInfo(ctx).fields
        return CategoryWriter_VolumeData3dInfo(ctx, 1, CategoryDescImpl("volume_data_3d_info", field_desc))


def number_field_volume3d_info(
    *,
    name: str,
    value: Callable[[VolumeInfo, int], Optional[Union[int, float]]],
    dtype: np.dtype,
    encoder: Callable[[VolumeInfo], BinaryCIFEncoder],
    presence: Optional[Callable[[VolumeInfo, int], Optional[ValuePresenceEnum]]] = None,
) -> FieldDesc:
    return number_field(name=name, value=value, dtype=dtype, encoder=encoder, presence=presence)

def string_field_volume3d_info(
    *,
    name: str,
    value: Callable[[VolumeInfo, int], Optional[str]],
    presence: Optional[Callable[[VolumeInfo, int], Optional[ValuePresenceEnum]]] = None,
) -> FieldDesc:
    return string_field(name=name, value=value, presence=presence)


class Fields_VolumeData3dInfo:
    # TODO: in times of peace implement it such that the data '_d' comes as parameter instead of constructor
    # Used _d in this version of the code for sanity check and type safety on lambda
    def __init__(self, _d: VolumeInfo):
        byte_array = lambda _: BinaryCIFEncoder([BYTE_ARRAY_CIF_ENCODER])

        self.fields: list[FieldDesc] = [            
            string_field(name="name", value=lambda d, i: _d.name),
            # TODO: would be nice to use i as index of axis order instead of index in the

            # axis order
            number_field_volume3d_info(name="axis_order[0]", value=lambda d, i: 0, encoder=byte_array, dtype='i4'),
            number_field_volume3d_info(name="axis_order[1]", value=lambda d, i: 1, encoder=byte_array, dtype='i4'),
            number_field_volume3d_info(name="axis_order[2]", value=lambda d, i: 2, encoder=byte_array, dtype='i4'),

            # origin
            number_field_volume3d_info(name="origin[0]", value=lambda d, i: _d.origin[0], encoder=byte_array, dtype='f4'),
            number_field_volume3d_info(name="origin[1]", value=lambda d, i: _d.origin[1], encoder=byte_array, dtype='f4'),
            number_field_volume3d_info(name="origin[2]", value=lambda d, i: _d.origin[2], encoder=byte_array, dtype='f4'),

            # dimensions
            number_field_volume3d_info(name="dimensions[0]", value=lambda d, i: _d.dimensions[0], encoder=byte_array, dtype='f4'),
            number_field_volume3d_info(name="dimensions[1]", value=lambda d, i: _d.dimensions[1], encoder=byte_array, dtype='f4'),
            number_field_volume3d_info(name="dimensions[2]", value=lambda d, i: _d.dimensions[2], encoder=byte_array, dtype='f4'),

            # sampling
            number_field_volume3d_info(name="sample_rate", value=lambda d, i: _d.box.downsampling_rate, encoder=byte_array, dtype='i4'),
            number_field_volume3d_info(name="sample_count[0]", value=lambda d, i: _d.grid_size[0], encoder=byte_array, dtype='i4'),
            number_field_volume3d_info(name="sample_count[1]", value=lambda d, i: _d.grid_size[1], encoder=byte_array, dtype='i4'),
            number_field_volume3d_info(name="sample_count[2]", value=lambda d, i: _d.grid_size[2], encoder=byte_array, dtype='i4'),

            # spacegroup
            number_field_volume3d_info(name="spacegroup_number", value=lambda d, i: 1, encoder=byte_array, dtype='i4'),
            number_field_volume3d_info(name="spacegroup_cell_size[0]", value=lambda d, i: _d.cell_size[0], encoder=byte_array, dtype='f8'),
            number_field_volume3d_info(name="spacegroup_cell_size[1]", value=lambda d, i: _d.cell_size[1], encoder=byte_array, dtype='f8'),
            number_field_volume3d_info(name="spacegroup_cell_size[2]", value=lambda d, i: _d.cell_size[2], encoder=byte_array, dtype='f8'),
            number_field_volume3d_info(name="spacegroup_cell_angles[0]", value=lambda d, i: 90, encoder=byte_array, dtype='f8'),
            number_field_volume3d_info(name="spacegroup_cell_angles[1]", value=lambda d, i: 90, encoder=byte_array, dtype='f8'),
            number_field_volume3d_info(name="spacegroup_cell_angles[2]", value=lambda d, i: 90, encoder=byte_array, dtype='f8'),

            # misc
            number_field_volume3d_info(name="mean_source", value=lambda d, i: _d.metadata.mean(1), encoder=byte_array, dtype='f8'),
            number_field_volume3d_info(name="mean_sampled", value=lambda d, i: _d.metadata.mean(_d.box.downsampling_rate), encoder=byte_array, dtype='f8'),
            number_field_volume3d_info(name="sigma_source", value=lambda d, i: _d.metadata.std(1), encoder=byte_array, dtype='f8'),
            number_field_volume3d_info(name="sigma_sampled", value=lambda d, i: _d.metadata.std(_d.box.downsampling_rate), encoder=byte_array, dtype='f8'),

            number_field_volume3d_info(name="min_source", value=lambda d, i: _d.metadata.min(1), encoder=byte_array, dtype='f8'),
            number_field_volume3d_info(name="min_sampled", value=lambda d, i: _d.metadata.min(_d.box.downsampling_rate), encoder=byte_array, dtype='f8'),
            number_field_volume3d_info(name="max_source", value=lambda d, i: _d.metadata.max(1), encoder=byte_array, dtype='f8'),
            number_field_volume3d_info(name="max_sampled", value=lambda d, i: _d.metadata.max(_d.box.downsampling_rate), encoder=byte_array, dtype='f8'),
        ]