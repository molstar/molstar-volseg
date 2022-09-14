from pprint import pprint
from typing import Callable, Optional, Union

import numpy as np
from ciftools.binary.encoding.impl.binary_cif_encoder import BinaryCIFEncoder
from ciftools.cif_format.value_presence import ValuePresenceEnum
from ciftools.writer.base import FieldDesc
from ciftools.writer.fields import number_field, string_field

from volume_server.src.preprocessed_volume_to_cif.implementations.ciftools_converter.Categories.volume_data_3d_info.volume_info import \
    VolumeInfo

from ciftools.binary.encoding.impl.encoders.byte_array import BYTE_ARRAY_CIF_ENCODER


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

            # TODO: origin/dimensions are currently incorrect, need to update VolumeInfo for this to work
            # origin
            number_field_volume3d_info(name="origin[0]", value=lambda d, i: _d.metadata.origin()[0] / _d.cell_size[0], encoder=byte_array, dtype='f4'),
            number_field_volume3d_info(name="origin[1]", value=lambda d, i: _d.metadata.origin()[1] / _d.cell_size[1], encoder=byte_array, dtype='f4'),
            number_field_volume3d_info(name="origin[2]", value=lambda d, i: _d.metadata.origin()[2] / _d.cell_size[2], encoder=byte_array, dtype='f4'),

            # dimensions
            number_field_volume3d_info(name="dimensions[0]", value=lambda d, i: _d.dimensions[0], encoder=byte_array, dtype='f4'),
            number_field_volume3d_info(name="dimensions[1]", value=lambda d, i: _d.dimensions[1], encoder=byte_array, dtype='f4'),
            number_field_volume3d_info(name="dimensions[2]", value=lambda d, i: _d.dimensions[2], encoder=byte_array, dtype='f4'),

            # sampling
            number_field_volume3d_info(name="sample_rate", value=lambda d, i: _d.downsampling, encoder=byte_array, dtype='i4'),
            # NOTE: currently need to do +1 on the grid size as it is "inclusive"
            number_field_volume3d_info(name="sample_count[0]", value=lambda d, i: _d.grid_size[0] + 1, encoder=byte_array, dtype='i4'),
            number_field_volume3d_info(name="sample_count[1]", value=lambda d, i: _d.grid_size[1] + 1 , encoder=byte_array, dtype='i4'),
            number_field_volume3d_info(name="sample_count[2]", value=lambda d, i: _d.grid_size[2] + 1, encoder=byte_array, dtype='i4'),

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
            number_field_volume3d_info(name="mean_sampled", value=lambda d, i: _d.metadata.mean(_d.downsampling), encoder=byte_array, dtype='f8'),
            number_field_volume3d_info(name="sigma_source", value=lambda d, i: _d.metadata.std(1), encoder=byte_array, dtype='f8'),
            number_field_volume3d_info(name="sigma_sampled", value=lambda d, i: _d.metadata.std(_d.downsampling), encoder=byte_array, dtype='f8'),

            number_field_volume3d_info(name="min_source", value=lambda d, i: _d.min_source, encoder=byte_array, dtype='f8'),
            number_field_volume3d_info(name="min_sampled", value=lambda d, i: _d.min_downsampled, encoder=byte_array, dtype='f8'),
            number_field_volume3d_info(name="max_source", value=lambda d, i: _d.max_source, encoder=byte_array, dtype='f8'),
            number_field_volume3d_info(name="max_sampled", value=lambda d, i: _d.max_downsampled, encoder=byte_array, dtype='f8'),
        ]