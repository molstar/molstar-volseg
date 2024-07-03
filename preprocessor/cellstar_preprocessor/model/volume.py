from dataclasses import dataclass

import dask.array as da
import numpy as np
from cellstar_db.models import (
    AxisName,
    InputKind,
    QuantizationDtype,
    SamplingBox,
    SpatialAxisUnit,
    TimeAxisUnit,
    VolumeChannelAnnotation,
    VolumeDescriptiveStatistics,
    VolumeExtraData,
)
from cellstar_preprocessor.flows.constants import (
    DEFAULT_ORIGINAL_AXIS_ORDER,
    DEFAULT_SOURCE_AXES_UNITS,
    QUANTIZATION_DATA_DICT_ATTR_NAME,
)
from cellstar_preprocessor.flows.volume.helper_methods import get_axis_order_mrcfile
from cellstar_preprocessor.model.common import hex_to_rgba_normalized
from cellstar_preprocessor.model.internal_data import InternalData
from cellstar_preprocessor.tools.quantize_data.quantize_data import (
    decode_quantized_data,
)


@dataclass
class InternalVolume(InternalData):
    volume_force_dtype: str
    quantize_dtype_str: QuantizationDtype
    quantize_downsampling_levels: tuple
    custom_data: VolumeExtraData | None = None
    map_header: object | None = None

    def get_original_axis_order(self) -> list[AxisName]:
        if self.input_kind == InputKind.map:
            return get_axis_order_mrcfile(self.map_header)

        elif self.input_kind == InputKind.omezarr:
            axes = self.get_omezarr_wrapper().get_image_multiscale().axes
            if len(axes) == 5:
                return [AxisName.t, AxisName.c] + DEFAULT_ORIGINAL_AXIS_ORDER
            elif len(axes) == 4:
                return [AxisName.c] + DEFAULT_ORIGINAL_AXIS_ORDER
            else:
                raise Exception(f"Axes number {len(axes)} is not supported")

    def get_source_axes_units(
        self,
    ) -> dict[AxisName, SpatialAxisUnit | TimeAxisUnit | None]:
        if self.input_kind == InputKind.map:
            # map always in angstroms
            return DEFAULT_SOURCE_AXES_UNITS
        elif self.input_kind == InputKind.omezarr:
            w = self.get_omezarr_wrapper()
            multiscale = w.get_image_multiscale()
            axes = multiscale.axes
            if len(axes) == 5:
                return {
                    AxisName.t: (
                        axes[0].unit
                        if axes[0].unit is not None
                        else TimeAxisUnit.millisecond
                    ),
                    AxisName.c: None,
                    AxisName.x: (
                        axes[2].unit
                        if axes[2].unit is not None
                        else SpatialAxisUnit.angstrom
                    ),
                    AxisName.y: (
                        axes[3].unit
                        if axes[3].unit is not None
                        else SpatialAxisUnit.angstrom
                    ),
                    AxisName.z: (
                        axes[4].unit
                        if axes[4].unit is not None
                        else SpatialAxisUnit.angstrom
                    ),
                }
            elif len(axes) == 4:
                return {
                    AxisName.t: TimeAxisUnit.millisecond,
                    AxisName.c: None,
                    AxisName.x: (
                        axes[1].unit
                        if axes[1].unit is not None
                        else SpatialAxisUnit.angstrom
                    ),
                    AxisName.y: (
                        axes[2].unit
                        if axes[2].unit is not None
                        else SpatialAxisUnit.angstrom
                    ),
                    AxisName.z: (
                        axes[3].unit
                        if axes[3].unit is not None
                        else SpatialAxisUnit.angstrom
                    ),
                }
            else:
                raise Exception(f"Axes number {len(axes)} is not supported")

    def get_channel_ids(self):
        v = self.get_volume_data_group()
        self.get_zarr_root()
        first_resolution = sorted(v.group_keys())[0]
        first_time: str = sorted(v[first_resolution].group_keys())[0]
        return v[first_resolution][first_time].array_keys()

    def get_grid_dimensions(self):
        return self.get_first_channel_array(self.get_volume_data_group()).shape

    def get_volume_sampling_info(self):
        volume_data_group = self.get_volume_data_group()
        origin = self.get_origin()
        voxel_sizes = self.get_voxel_sizes_in_downsamplings()

        sampling_info_dict = self.get_metadata().volumes.sampling_info
        for res_gr_name, res_gr in volume_data_group.groups():
            # TODO: grid dimensions get
            sampling_info_dict.boxes[res_gr_name] = SamplingBox(
                origin=origin,
                voxel_size=voxel_sizes[int(res_gr_name)],
                grid_dimensions=self.get_grid_dimensions(),
            )

            sampling_info_dict.descriptive_statistics[res_gr_name] = {}

            for time_gr_name, time_gr in res_gr.groups():
                first_group_key = sorted(time_gr.array_keys())[0]

                sampling_info_dict.boxes[res_gr_name].grid_dimensions = time_gr[
                    first_group_key
                ].shape
                # sampling_info_dict['boxes'][res_gr_name]['force_dtype'] = time_gr[first_group_key].dtype.str

                sampling_info_dict.descriptive_statistics[res_gr_name][
                    time_gr_name
                ] = {}
                for channel_arr_name, channel_arr in time_gr.arrays():
                    assert (
                        sampling_info_dict.boxes[res_gr_name].grid_dimensions
                        == channel_arr.shape
                    )
                    # assert sampling_info_dict['boxes'][res_gr_name]['force_dtype'] == channel_arr.dtype.str

                    arr_view = channel_arr[...]
                    if QUANTIZATION_DATA_DICT_ATTR_NAME in channel_arr.attrs:
                        data_dict = channel_arr.attrs[QUANTIZATION_DATA_DICT_ATTR_NAME]
                        data_dict["data"] = arr_view
                        arr_view = decode_quantized_data(data_dict)
                        if isinstance(arr_view, da.Array):
                            arr_view = arr_view.compute()

                    mean_val = float(str(np.mean(arr_view)))
                    std_val = float(str(np.std(arr_view)))
                    max_val = float(str(arr_view.max()))
                    min_val = float(str(arr_view.min()))

                    sampling_info_dict.descriptive_statistics[res_gr_name][
                        time_gr_name
                    ][channel_arr_name] = VolumeDescriptiveStatistics(
                        mean=mean_val, min=min_val, max=max_val, std=std_val
                    )

        return sampling_info_dict

    def set_volume_custom_data(self):
        r = self.get_zarr_root()
        if "extra_data" in r.attrs:
            if "volume" in r.attrs["extra_data"]:
                self.custom_data = r.attrs["extra_data"]["volume"]
            else:
                self.custom_data = {}
        else:
            self.custom_data = {}

    # TODO: use the same for other input types
    def set_volume_channel_annotations(self):
        a = self.get_annotations()
        if self.input_kind == InputKind.omezarr:
            w = self.get_omezarr_wrapper()
            channels = w.get_omero_channels()
            volume_channels_annotations: list[VolumeChannelAnnotation] = []
            for idx, channel in enumerate(channels):
                channel_id = str(idx) if channel.label is None else channel.label
                volume_channels_annotations.append(
                    VolumeChannelAnnotation(
                        channel_id=channel_id,
                        color=hex_to_rgba_normalized(channel.color),
                        label=channel_id,
                    )
                )

        a.volume_channels_annotations = volume_channels_annotations
        self.set_annotations(a)
        return volume_channels_annotations
