from dataclasses import dataclass
import gc
import math
from cellstar_preprocessor.flows.common import compute_downsamplings_to_be_stored, compute_number_of_downsampling_steps
from cellstar_preprocessor.model.ometiff import read_ometiff_pyometiff
import zarr
# from cellstar_preprocessor.flows.common import set_ometiff_source_metadata
from cellstar_db.file_system.constants import VOLUME_DATA_GROUPNAME
from cellstar_preprocessor.flows.zarr_methods import create_dataset_wrapper, get_downsamplings
import dask.array as da
import numpy as np
import mrcfile
from dask_image.ndfilters import convolve as dask_convolve

from cellstar_db.models import (
    AxisName,
    DownsamplingLevelInfo,
    ExtraData,
    AssetKind,
    PreparedVolume,
    PreparedVolumeData,
    PreparedVolumeMetadata,
    QuantizationDtype,
    QuantizationInfo,
    SamplingBox,
    SpatialAxisUnit,
    TimeAxisUnit,
    TimeInfo,
    VolumeChannelAnnotation,
    VolumeDescriptiveStatistics,
    VolumeExtraData,
    VolumeSamplingInfo,
    VolumesMetadata,
)
from cellstar_preprocessor.flows.constants import (
    DEFAULT_CHANNEL_ID,
    DEFAULT_CHANNEL_IDS_MAPPING,
    DEFAULT_ORIGINAL_AXIS_ORDER_3D,
    DEFAULT_SOURCE_AXES_UNITS,
    DEFAULT_TIME_UNITS,
    DOWNSAMPLING_KERNEL,
    MIN_GRID_SIZE,
    QUANTIZATION_DATA_DICT_ATTR_NAME,
)
from cellstar_preprocessor.flows.volume.helper_methods import generate_kernel_3d_arr, get_axis_order_mrcfile, normalize_axis_order_mrcfile, store_volume_data_in_zarr
from cellstar_preprocessor.model.common import hex_to_rgba_normalized
from cellstar_preprocessor.model.internal_data import InternalData
from cellstar_preprocessor.tools.quantize_data.quantize_data import (
    decode_quantized_data,
)
import dask.array as da

@dataclass
class InternalVolume(InternalData):
    volume_force_dtype: str
    quantize_dtype_str: QuantizationDtype
    quantize_downsampling_levels: tuple
    custom_data: VolumeExtraData | None = None
    map_header: object | None = None
    prepared: PreparedVolume | None = None

    def get_first_channel_array(self, data_group: zarr.Group) -> zarr.Array:
        first_time_gr = self.get_first_time_group(data_group)
        first_channel: str = sorted(first_time_gr.array_keys())[0]
        return first_time_gr[first_channel]
    
    def downsample(self):
        match self.input_kind:
            case AssetKind.omezarr:
                pass
            case _:
                orig_res_gr: zarr.Group = self.get_first_resolution_group(self.get_volume_data_group())
                for time, timegr in orig_res_gr.groups():
                    timegr: zarr.Group
                    for channel_id, channel_arr in timegr.arrays():
                        # NOTE: skipping convolve if one of dimensions is 1
                        if 1 in channel_arr.shape:
                            print(
                                f"Downsampling skipped for volume channel {channel_id}, timeframe {time} since one of the dimensions is equal to 1"
                            )
                            continue

                        original_data_arr = orig_res_gr[str(time)][
                            str(channel_id)
                        ]
                        if QUANTIZATION_DATA_DICT_ATTR_NAME in original_data_arr.attrs:
                            data_dict = QuantizationInfo.model_validate(original_data_arr.attrs[QUANTIZATION_DATA_DICT_ATTR_NAME])
                            data_dict.data = da.from_zarr(url=original_data_arr)
                            dask_arr: da.Array = decode_quantized_data(data_dict)
                        else:
                            dask_arr = da.from_zarr(
                                url=original_data_arr, chunks=original_data_arr.chunks
                            )

                        kernel = generate_kernel_3d_arr(list(DOWNSAMPLING_KERNEL))
                        current_level_data = dask_arr

                        # 1. compute number of downsampling steps based on internal_volume.downsampling
                        # 2. compute list of ratios of downsamplings to be stored based on internal_volume.downsampling
                        # 3. if ratio is in list, store it

                        # downsampling_steps = 8
                        downsampling_steps = compute_number_of_downsampling_steps(
                            downsampling_parameters=self.downsampling_parameters,
                            min_grid_size=MIN_GRID_SIZE,
                            input_grid_size=math.prod(dask_arr.shape),
                            factor=2**3,
                            force_dtype=dask_arr.dtype,
                        )

                        ratios_to_be_stored = compute_downsamplings_to_be_stored(
                            downsampling_parameters=self.downsampling_parameters,
                            number_of_downsampling_steps=downsampling_steps,
                            input_grid_size=math.prod(dask_arr.shape),
                            factor=2**3,
                            dtype=dask_arr.dtype,
                        )
                        for i in range(downsampling_steps):
                            current_ratio = 2 ** (i + 1)
                            assert len(current_level_data.shape) == 3, 'Data must be 3D'
                            downsampled_data = dask_convolve(
                                current_level_data, kernel, mode="mirror", cval=0.0
                            )
                            downsampled_data = downsampled_data[::2, ::2, ::2]

                            if current_ratio in ratios_to_be_stored:
                                store_volume_data_in_zarr(
                                    data=downsampled_data,
                                    volume_data_group=self.get_volume_data_group(),
                                    params_for_storing=self.params_for_storing,
                                    force_dtype=self.volume_force_dtype,
                                    resolution=current_ratio,
                                    timeframe_index=time,
                                    channel_id=channel_id,
                                )

                            current_level_data = downsampled_data
                        print("Volume downsampled")

    
    def _prepare_ometiff(self):
        # NOTE: just creates wrapper and calls wrapper methods
        w = self.get_ometiff_wrapper()
        return w.prepare_volume_data()
    
    def _prepare_omezarr(self):
        w = self.get_omezarr_wrapper()
        return w.prepare_volume_data()
      
    def _prepare_map(self):
        # TODO: open map as memmap - separate helper function returning context
        with mrcfile.mmap(str(self.input_path.resolve()), "r+") as mrc_original:
            data: np.memmap = mrc_original.data
            if self.volume_force_dtype is not None:
                data = data.astype(self.volume_force_dtype)
            else:
                self.volume_force_dtype = data.dtype

            # temp hack to process rec files with cella 0 0 0
            # if mrc_original.header.cella.x == 0 and mrc_original.header.cella.y == 0 and mrc_original.header.cella.z == 0:
            if self.custom_data.voxel_size is not None:
                # TODO: this is probably wrong
                mrc_original.voxel_size = 1 * self.custom_data.voxel_size

            header = mrc_original.header
            # single channel and timeframe

            dask_arr = da.from_array(data)
            dask_arr = normalize_axis_order_mrcfile(dask_arr=dask_arr, mrc_header=header)
            self.map_header = header

        return PreparedVolume(
            data=[PreparedVolumeData(
                timeframe_index=0,
                channel_num=0,
                resolution=1,
                data=dask_arr,
                size=dask_arr.nbytes
            )],
            metadata=PreparedVolumeMetadata(
                channel_nums=[0],
                timeframe_indices=[0],
                resolutions=[1]
            )
        )

    def prepare(self):
        match self.input_kind:
            case AssetKind.omezarr:
                self.prepared = self._prepare_omezarr()
            case AssetKind.ometiff_image: 
                self.prepared = self._prepare_ometiff()
            case AssetKind.map:
                self.prepared = self._prepare_map()
            case _:
                raise NotImplementedError(f'{self.input_kind} is not supported')
    
    def store(self):
        root = self.get_zarr_root()
        volume_data_gr: zarr.Group = root.create_group(VOLUME_DATA_GROUPNAME)
        preprared_data = self.prepared.data
        
        for d in preprared_data:
            store_volume_data_in_zarr(
                data=d.data,
                volume_data_group=volume_data_gr,
                params_for_storing=self.params_for_storing,
                force_dtype=self.volume_force_dtype,
                resolution=d.resolution,
                timeframe_index=d.timeframe_index,
                # custom data?
                channel_id=d.channel_id,
            )
    
    def get_time_units(self):
        if self.input_kind in [AssetKind.map, AssetKind.ometiff_image]:
            return DEFAULT_TIME_UNITS
    
    def remove_downsamplings(self):
        volume_data_gr = self.get_volume_data_group()
        original_resolution = self.get_first_resolution_group(volume_data_gr)
        for info in get_downsamplings(volume_data_gr):
            if info.available:
                res = info.level
            size_of_data_for_lvl_mb = self.prepared.compute_size_for_downsampling_level(res)
            print(f"size of data for lvl in mb: {size_of_data_for_lvl_mb}")
            if (
                (self.downsampling_parameters.max_size_per_downsampling_lvl_mb
                and size_of_data_for_lvl_mb
                > self.downsampling_parameters.max_size_per_downsampling_lvl_mb)
                or
                (
                    self.downsampling_parameters.min_size_per_downsampling_lvl_mb
                    and size_of_data_for_lvl_mb < self.downsampling_parameters.min_size_per_downsampling_lvl_mb
                )
            ):
                print(f"Volume data for resolution {res} was removed")
                del volume_data_gr[res]
                gc.collect()
            
            if self.downsampling_parameters.max_downsampling_level is not None:
                for downsampling, downsampling_gr in volume_data_gr.groups():
                    if int(downsampling) > self.downsampling_parameters.max_downsampling_level:
                        del volume_data_gr[downsampling]
                        gc.collect()
                        print(f"Data for downsampling {downsampling} removed for volume")

            if self.downsampling_parameters.min_downsampling_level is not None:
                for downsampling, downsampling_gr in volume_data_gr.groups():
                    if (
                        int(downsampling) < self.downsampling_parameters.min_downsampling_level
                        and downsampling != original_resolution
                    ):
                        del volume_data_gr[downsampling]
                        gc.collect()
                        print(f"Data for downsampling {downsampling} removed for volume")

            if len(sorted(volume_data_gr.group_keys())) == 0:
                raise Exception(
                    f"No downsamplings will be saved: max_size_per_downsampling_lvl_mb {self.downsampling_parameters.max_size_per_downsampling_lvl_mb} is too low"
                )
    
    def remove_original_resolution(self):
        m = self.get_metadata()
        if self.downsampling_parameters.remove_original_resolution:
            first_resolution = str(self.get_first_resolution_group(self.get_volume_data_group()).name)
            del self.get_volume_data_group()[first_resolution]
            print(f"Original resolution ({first_resolution}) for volume data removed")

            current_levels = m.volumes.sampling_info.spatial_downsampling_levels
    
            for i, item in enumerate(current_levels):
                if item.level == first_resolution:
                    current_levels[i].available = False
            # fix metadata
            m.volumes.sampling_info.spatial_downsampling_levels = current_levels
            
        self.set_metadata(m)
    
    def set_volumes_metadata(self):
        # TODO: add options for different input kinds if necessary
        m = self.get_metadata()
        start_time, end_time = self.get_start_end_time(self.get_volume_data_group())
        m.volumes = VolumesMetadata(
            channel_ids=self.get_channel_ids(),
            time_info=TimeInfo(
                kind="range", start=start_time, end=end_time, units=self.get_time_units()
            ),
            sampling_info=VolumeSamplingInfo(
                spatial_downsampling_levels=get_downsamplings(data_group=self.get_volume_data_group()),
                boxes={},
                descriptive_statistics={},
                time_transformations=[],
                source_axes_units=self.get_source_axes_units(),
                original_axis_order=self.get_original_axis_order(),
            ),
        )
        self.set_boxes_and_descriptive_statistics()
        m = self.get_metadata()
        self.set_metadata(m)

    def get_original_axis_order(self) -> list[AxisName]:
        if self.input_kind == AssetKind.map:
            return get_axis_order_mrcfile(self.map_header)

        elif self.input_kind == AssetKind.omezarr:
            axes = self.get_omezarr_wrapper().get_image_multiscale().axes
            if len(axes) == 5:
                return [AxisName.t, AxisName.c] + DEFAULT_ORIGINAL_AXIS_ORDER_3D
            elif len(axes) == 4:
                return [AxisName.c] + DEFAULT_ORIGINAL_AXIS_ORDER_3D
            else:
                raise Exception(f"Axes number {len(axes)} is not supported")
        
        elif self.input_kind == AssetKind.ometiff_image:
            # TODO: ometiff wrapper and make it work with it
            return DEFAULT_ORIGINAL_AXIS_ORDER_3D
        
    def get_source_axes_units(
        self,
    ) -> dict[AxisName, SpatialAxisUnit | TimeAxisUnit | None]:
        if self.input_kind in [AssetKind.map, AssetKind.ometiff_image]:
            # map always in angstroms
            return DEFAULT_SOURCE_AXES_UNITS
        elif self.input_kind == AssetKind.omezarr:
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
        if self.custom_data.channel_ids_mapping:
            return list(self.custom_data.channel_ids_mapping.values())
        else:
            return self.prepared.metadata.channel_ids
            # v = self.get_volume_data_group()
            
            # self.get_zarr_root()
            # first_resolution = sorted(v.group_keys())[0]
            # first_time: str = sorted(v[first_resolution].group_keys())[0]
            # return v[first_resolution][first_time].array_keys()

    def get_grid_dimensions(self):
        return self.get_first_channel_array(self.get_volume_data_group()).shape
    
    def set_boxes_and_descriptive_statistics(self):
        m = self.get_metadata()
        volume_data_group = self.get_volume_data_group()
        origin = self.get_origin()
        voxel_sizes = self.get_voxel_sizes_in_downsamplings()

        for res_gr_name, res_gr in volume_data_group.groups():
            # TODO: grid dimensions get
            m.volumes.sampling_info.boxes[res_gr_name] = SamplingBox(
                origin=origin,
                # empty voxel_sizes for ometiff
                voxel_size=voxel_sizes[int(res_gr_name)],
                grid_dimensions=self.get_grid_dimensions(),
            )

            m.volumes.sampling_info.descriptive_statistics[res_gr_name] = {}

            for time_gr_name, time_gr in res_gr.groups():
                first_group_key = sorted(time_gr.array_keys())[0]

                m.volumes.sampling_info.boxes[res_gr_name].grid_dimensions = time_gr[
                    first_group_key
                ].shape
                # sampling_info_dict['boxes'][res_gr_name]['force_dtype'] = time_gr[first_group_key].dtype.str

                m.volumes.sampling_info.descriptive_statistics[res_gr_name][
                    time_gr_name
                ] = {}
                for channel_arr_name, channel_arr in time_gr.arrays():
                    assert (
                        m.volumes.sampling_info.boxes[res_gr_name].grid_dimensions
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

                    m.volumes.sampling_info.descriptive_statistics[res_gr_name][
                        time_gr_name
                    ][channel_arr_name] = VolumeDescriptiveStatistics(
                        mean=mean_val, min=min_val, max=max_val, std=std_val
                    )

        self.set_metadata(m)

    def set_custom_data(self):
        r = self.get_zarr_root()
        if "extra_data" in r.attrs:
            if "volume" in r.attrs["extra_data"]:
                self.custom_data = VolumeExtraData.model_validate(r.attrs["extra_data"]["volume"])
            else:
                self.custom_data = VolumeExtraData()
        else:
            self.custom_data = VolumeExtraData()
            
    def postprepare(self):
        '''
        Sets channel ids in prepared data; possibly other things
        '''
        
        # set from channel ids mapping
        # None prepared
        self.prepared.metadata.channel_ids = list(self.custom_data.channel_ids_mapping.values())
        # breaks
        for idx, item in enumerate(self.prepared.data):
            item.channel_id = self.custom_data.channel_ids_mapping[str(item.channel_num)]
            self.prepared.data[idx] = item
            
    def set_channels_ids_mapping(self):
        if self.custom_data.channel_ids_mapping is None:
            # not provided, try to get from metadata if omezarr
            if self.input_kind == AssetKind.omezarr:
                w = self.get_omezarr_wrapper()
                self.custom_data.channel_ids_mapping = w.create_channel_ids_mapping()
                
            elif self.input_kind == AssetKind.map:
                self.custom_data.channel_ids_mapping = DEFAULT_CHANNEL_IDS_MAPPING
            elif self.input_kind == AssetKind.ometiff_image:
                w = self.get_ometiff_wrapper()
                self.custom_data.channel_ids_mapping = w.create_channel_ids_mapping()
            else:
                raise NotImplementedError(f"{self.input_kind} not supported")
    
    def create_artificial_channel_anntoations_from_data(self):
        # no color just channel id and label
        if self.input_kind == AssetKind.omezarr:
            raise NotImplementedError(f'Support for input kind {self.input_kind} has not been implemented')
        else:
            raise NotImplementedError(f'Support for input kind {self.input_kind} has not been implemented')
    
    # TODO: use the same for other input types
    # should get channel ids from custom data if provided, if not - from data
    # TODO: other input types as well
    # TODO: should be a way to provided volume channel annotations
    # as well to preprocessor (desired colors etc.)
    def set_volume_channel_annotations(self):
        a = self.get_annotations()
        kind = self.input_kind
        volume_channels_annotations: list[VolumeChannelAnnotation] = []
        if self.custom_data.custom_volume_channel_annotations is not None:
            volume_channels_annotations = self.custom_data.custom_volume_channel_annotations.copy()
        if kind == AssetKind.omezarr:
            w = self.get_omezarr_wrapper()
            if w.get_omero_channels() is not None:
                for idx, channel in enumerate(w.get_omero_channels()):
                    channel_id = str(idx) if channel.label is None else channel.label
                    volume_channels_annotations.append(
                        VolumeChannelAnnotation(
                            channel_id=channel_id,
                            color=hex_to_rgba_normalized(channel.color),
                            label=channel_id,
                        )
                    )
            else:
                volume_channels_annotations = self.create_artificial_channel_anntoations_from_data()
                
        elif kind == AssetKind.ometiff_image:
            w = self.get_ometiff_wrapper()
            channels: list[str] = w.channels
            if channels is not None:
                for idx, channel_id in enumerate(channels):
                    volume_channels_annotations.append(
                        VolumeChannelAnnotation(
                            channel_id=channel_id,
                            color=None,
                            # color=hex_to_rgba_normalized(channel.color),
                            label=channel_id,
                        ))

                
        else:
            raise NotImplementedError(f'Support for input kind {kind} has not been implemented')

        a.volume_channels_annotations = volume_channels_annotations
        self.set_annotations(a)
        return volume_channels_annotations
