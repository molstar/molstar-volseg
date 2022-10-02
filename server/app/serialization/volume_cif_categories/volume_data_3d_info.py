from ciftools.writer.base import FieldDesc
from ciftools.writer.fields import number_field, string_field

from app.serialization.data.volume_info import VolumeInfo
from app.serialization.volume_cif_categories.common import CategoryWriterProviderBase
from app.serialization.volume_cif_categories import encoders


class CategoryWriterProvider_VolumeData3dInfo(CategoryWriterProviderBase[VolumeInfo]):
    category_name = 'volume_data_3d_info'

    def get_row_count(self, ctx: VolumeInfo) -> int:
        return 1

    def get_field_descriptors(self, ctx: VolumeInfo) -> list[FieldDesc]:
        byte_array = encoders.bytearray_encoder
        return [
            string_field(name="name", value=lambda d, i: ctx.name),
            # TODO: would be nice to use i as index of axis order instead of index in the
            # axis order
            number_field(name="axis_order[0]", value=lambda d, i: 0, encoder=byte_array, dtype="i4"),
            number_field(name="axis_order[1]", value=lambda d, i: 1, encoder=byte_array, dtype="i4"),
            number_field(name="axis_order[2]", value=lambda d, i: 2, encoder=byte_array, dtype="i4"),
            # origin
            number_field(name="origin[0]", value=lambda d, i: ctx.origin[0], encoder=byte_array, dtype="f4"),
            number_field(name="origin[1]", value=lambda d, i: ctx.origin[1], encoder=byte_array, dtype="f4"),
            number_field(name="origin[2]", value=lambda d, i: ctx.origin[2], encoder=byte_array, dtype="f4"),
            # dimensions
            number_field(name="dimensions[0]", value=lambda d, i: ctx.dimensions[0], encoder=byte_array, dtype="f4"),
            number_field(name="dimensions[1]", value=lambda d, i: ctx.dimensions[1], encoder=byte_array, dtype="f4"),
            number_field(name="dimensions[2]", value=lambda d, i: ctx.dimensions[2], encoder=byte_array, dtype="f4"),
            # sampling
            number_field(name="sample_rate", value=lambda d, i: ctx.box.downsampling_rate, encoder=byte_array, dtype="i4"),
            number_field(name="sample_count[0]", value=lambda d, i: ctx.grid_size[0], encoder=byte_array, dtype="i4"),
            number_field(name="sample_count[1]", value=lambda d, i: ctx.grid_size[1], encoder=byte_array, dtype="i4"),
            number_field(name="sample_count[2]", value=lambda d, i: ctx.grid_size[2], encoder=byte_array, dtype="i4"),
            # spacegroup
            number_field(name="spacegroup_number", value=lambda d, i: 1, encoder=byte_array, dtype="i4"),
            number_field(name="spacegroup_cell_size[0]", value=lambda d, i: ctx.cell_size[0], encoder=byte_array, dtype="f8"),
            number_field(name="spacegroup_cell_size[1]", value=lambda d, i: ctx.cell_size[1], encoder=byte_array, dtype="f8"),
            number_field(name="spacegroup_cell_size[2]", value=lambda d, i: ctx.cell_size[2], encoder=byte_array, dtype="f8"),
            number_field(name="spacegroup_cell_angles[0]", value=lambda d, i: 90, encoder=byte_array, dtype="f8"),
            number_field(name="spacegroup_cell_angles[1]", value=lambda d, i: 90, encoder=byte_array, dtype="f8"),
            number_field(name="spacegroup_cell_angles[2]", value=lambda d, i: 90, encoder=byte_array, dtype="f8"),
            # misc
            number_field(name="mean_source", value=lambda d, i: ctx.metadata.mean(1), encoder=byte_array, dtype="f8"),
            number_field(name="mean_sampled",value=lambda d, i: ctx.metadata.mean(ctx.box.downsampling_rate),encoder=byte_array,dtype="f8",),
            number_field(name="sigma_source", value=lambda d, i: ctx.metadata.std(1), encoder=byte_array, dtype="f8"),
            number_field(name="sigma_sampled",value=lambda d, i: ctx.metadata.std(ctx.box.downsampling_rate),encoder=byte_array,dtype="f8",),
            number_field(name="min_source", value=lambda d, i: ctx.metadata.min(1), encoder=byte_array, dtype="f8"),
            number_field(name="min_sampled",value=lambda d, i: ctx.metadata.min(ctx.box.downsampling_rate),encoder=byte_array,dtype="f8",),
            number_field(name="max_source", value=lambda d, i: ctx.metadata.max(1), encoder=byte_array, dtype="f8"),
            number_field(name="max_sampled",value=lambda d, i: ctx.metadata.max(ctx.box.downsampling_rate),encoder=byte_array,dtype="f8",),
        ]
