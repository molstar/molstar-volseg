from typing import Callable, Optional

import numpy as np
from ciftools.binary.encoding import BinaryCIFEncoder
from ciftools.cif_format import ValuePresenceEnum
from ciftools.writer.base import FieldDesc
from ciftools.writer.fields import number_field

from db.interface.i_preprocessed_medatada import IPreprocessedMetadata


def number_field_volume3d_info(
    *,
    name: str,
    value: Callable[[IPreprocessedMetadata, int], Optional[int | float]],
    dtype: np.dtype,
    encoder: Callable[[IPreprocessedMetadata], BinaryCIFEncoder],
    presence: Optional[Callable[[IPreprocessedMetadata, int], Optional[ValuePresenceEnum]]] = None,
) -> FieldDesc:
    return number_field(name=name, value=value, dtype=dtype, encoder=encoder, presence=presence)


class Fields_VolumeData3dInfo:
    def _axis(self, d: IPreprocessedMetadata, i: int):
        return i

    def _origin(self, d: IPreprocessedMetadata, i: int):
        return d.origin()[i]

    def __init__(self, encoder: BinaryCIFEncoder, dtype: np.dtype):
        self.fields: list[FieldDesc] = [
            # TODO: would be nice to use i as index of axis order instead of index in the

            number_field_volume3d_info(name="axis_order[0]", value=self._axis, encoder=lambda d: encoder, dtype=dtype),
            number_field_volume3d_info(name="axis_order[1]", value=self._axis, encoder=lambda d: encoder, dtype=dtype),
            number_field_volume3d_info(name="axis_order[2]", value=self._axis, encoder=lambda d: encoder, dtype=dtype),


            number_field_volume3d_info(name="origin[0]", value=self._origin, encoder=lambda d: encoder, dtype=dtype),
            number_field_volume3d_info(name="origin[1]", value=self._origin, encoder=lambda d: encoder, dtype=dtype),
            number_field_volume3d_info(name="origin[2]", value=self._origin, encoder=lambda d: encoder, dtype=dtype)
        ]


"""
    string<_vd3d_Ctx>('name', ctx => ctx.header.channels[ctx.channelIndex]),

    float64<_vd3d_Ctx>('dimensions[0]', ctx => ctx.grid.dimensions[0]),
    float64<_vd3d_Ctx>('dimensions[1]', ctx => ctx.grid.dimensions[1]),
    float64<_vd3d_Ctx>('dimensions[2]', ctx => ctx.grid.dimensions[2]),

    int32<_vd3d_Ctx>('sample_rate', ctx => ctx.sampleRate),
    int32<_vd3d_Ctx>('sample_count[0]', ctx => ctx.grid.sampleCount[0]),
    int32<_vd3d_Ctx>('sample_count[1]', ctx => ctx.grid.sampleCount[1]),
    int32<_vd3d_Ctx>('sample_count[2]', ctx => ctx.grid.sampleCount[2]),

    int32<_vd3d_Ctx>('spacegroup_number', ctx => ctx.header.spacegroup.number),

    float64<_vd3d_Ctx>('spacegroup_cell_size[0]', ctx => ctx.header.spacegroup.size[0], 3),
    float64<_vd3d_Ctx>('spacegroup_cell_size[1]', ctx => ctx.header.spacegroup.size[1], 3),
    float64<_vd3d_Ctx>('spacegroup_cell_size[2]', ctx => ctx.header.spacegroup.size[2], 3),

    float64<_vd3d_Ctx>('spacegroup_cell_angles[0]', ctx => ctx.header.spacegroup.angles[0], 3),
    float64<_vd3d_Ctx>('spacegroup_cell_angles[1]', ctx => ctx.header.spacegroup.angles[1], 3),
    float64<_vd3d_Ctx>('spacegroup_cell_angles[2]', ctx => ctx.header.spacegroup.angles[2], 3),

    float64<_vd3d_Ctx>('mean_source', ctx => ctx.globalValuesInfo.mean),
    float64<_vd3d_Ctx>('mean_sampled', ctx => ctx.sampledValuesInfo.mean),
    float64<_vd3d_Ctx>('sigma_source', ctx => ctx.globalValuesInfo.sigma),
    float64<_vd3d_Ctx>('sigma_sampled', ctx => ctx.sampledValuesInfo.sigma),
    float64<_vd3d_Ctx>('min_source', ctx => ctx.globalValuesInfo.min),
    float64<_vd3d_Ctx>('min_sampled', ctx => ctx.sampledValuesInfo.min),
    float64<_vd3d_Ctx>('max_source', ctx => ctx.globalValuesInfo.max),
    float64<_vd3d_Ctx>('max_sampled', ctx => ctx.sampledValuesInfo.max)
"""