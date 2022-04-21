from typing import Callable, Optional

import numpy as np
from ciftools.binary.encoding import BinaryCIFEncoder
from ciftools.cif_format import ValuePresenceEnum
from ciftools.writer.base import FieldDesc
from ciftools.writer.fields import number_field, string_field

from db.interface.i_preprocessed_medatada import IPreprocessedMetadata
from volume_server.preprocessed_volume_to_cif.implementations.ciftools_converter.Categories.volume_data_3d_info.volume_info import \
    VolumeInfo


def number_field_volume3d_info(
    *,
    name: str,
    value: Callable[[VolumeInfo, int], Optional[int | float]],
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
    def __init__(self, _d: VolumeInfo, encoder: BinaryCIFEncoder, dtype: np.dtype):
        self.fields: list[FieldDesc] = [
            string_field(name="name", value=lambda d, i: _d.name),
            # TODO: would be nice to use i as index of axis order instead of index in the

            # axis order
            number_field_volume3d_info(name="axis_order[0]", value=lambda d, i: 0, encoder=lambda d: encoder, dtype=dtype),
            number_field_volume3d_info(name="axis_order[1]", value=lambda d, i: 1, encoder=lambda d: encoder, dtype=dtype),
            number_field_volume3d_info(name="axis_order[2]", value=lambda d, i: 2, encoder=lambda d: encoder, dtype=dtype),

            # origin
            number_field_volume3d_info(name="origin[0]", value=lambda d, i: _d.metadata.origin()[0], encoder=lambda d: encoder, dtype=dtype),
            number_field_volume3d_info(name="origin[1]", value=lambda d, i: _d.metadata.origin()[1], encoder=lambda d: encoder, dtype=dtype),
            number_field_volume3d_info(name="origin[2]", value=lambda d, i: _d.metadata.origin()[2], encoder=lambda d: encoder, dtype=dtype),

            # dimensions
            number_field_volume3d_info(name="dimensions[0]", value=lambda d, i: _d.metadata.grid_dimensions()[0], encoder=lambda d: encoder, dtype=dtype),
            number_field_volume3d_info(name="dimensions[1]", value=lambda d, i: _d.metadata.grid_dimensions()[1], encoder=lambda d: encoder, dtype=dtype),
            number_field_volume3d_info(name="dimensions[2]", value=lambda d, i: _d.metadata.grid_dimensions()[2], encoder=lambda d: encoder, dtype=dtype),

            # sampling
            number_field_volume3d_info(name="sample_rate", value=lambda d, i: _d.downsampling, encoder=lambda d: encoder, dtype=dtype),
            number_field_volume3d_info(name="sample_count[0]", value=lambda d, i: _d.grid_size[0], encoder=lambda d: encoder, dtype=dtype),
            number_field_volume3d_info(name="sample_count[1]", value=lambda d, i: _d.grid_size[1], encoder=lambda d: encoder, dtype=dtype),
            number_field_volume3d_info(name="sample_count[2]", value=lambda d, i: _d.grid_size[2], encoder=lambda d: encoder, dtype=dtype),

            # spacegroup
            number_field_volume3d_info(name="spacegroup_number", value=lambda d, i: 0, encoder=lambda d: encoder, dtype=dtype),
            number_field_volume3d_info(name="spacegroup_cell_size[0]", value=lambda d, i: _d.metadata.voxel_size(_d.downsampling)[0], encoder=lambda d: encoder, dtype=dtype),
            number_field_volume3d_info(name="spacegroup_cell_size[1]", value=lambda d, i: _d.metadata.voxel_size(_d.downsampling)[1], encoder=lambda d: encoder, dtype=dtype),
            number_field_volume3d_info(name="spacegroup_cell_size[2]", value=lambda d, i: _d.metadata.voxel_size(_d.downsampling)[2], encoder=lambda d: encoder, dtype=dtype),
            number_field_volume3d_info(name="spacegroup_cell_angles[0]", value=lambda d, i: 90, encoder=lambda d: encoder, dtype=dtype),
            number_field_volume3d_info(name="spacegroup_cell_angles[1]", value=lambda d, i: 90, encoder=lambda d: encoder, dtype=dtype),
            number_field_volume3d_info(name="spacegroup_cell_angles[2]", value=lambda d, i: 90, encoder=lambda d: encoder, dtype=dtype),

            # misc
            number_field_volume3d_info(name="mean_source", value=lambda d, i: _d.metadata.mean(1), encoder=lambda d: encoder, dtype=dtype),
            number_field_volume3d_info(name="mean_sampled", value=lambda d, i: _d.metadata.mean(_d.downsampling), encoder=lambda d: encoder, dtype=dtype),
            number_field_volume3d_info(name="sigma_source", value=lambda d, i: _d.metadata.std(1), encoder=lambda d: encoder, dtype=dtype),
            number_field_volume3d_info(name="sigma_sampled", value=lambda d, i: _d.metadata.std(_d.downsampling), encoder=lambda d: encoder, dtype=dtype),
            # TODO: missing min_source and max_source
            number_field_volume3d_info(name="min_source", value=lambda d, i: _d.min_downsampled, encoder=lambda d: encoder, dtype=dtype),
            number_field_volume3d_info(name="min_sampled", value=lambda d, i: _d.min_downsampled, encoder=lambda d: encoder, dtype=dtype),
            number_field_volume3d_info(name="max_source", value=lambda d, i: _d.max_downsampled, encoder=lambda d: encoder, dtype=dtype),
            number_field_volume3d_info(name="max_sampled", value=lambda d, i: _d.max_downsampled, encoder=lambda d: encoder, dtype=dtype),
        ]