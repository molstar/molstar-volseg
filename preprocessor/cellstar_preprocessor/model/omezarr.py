from pydantic.dataclasses import dataclass
import gc
from pathlib import Path
from typing import Any

import zarr
from cellstar_db.models import (
    AxisName,
    OMEZarrAttrs,
    PreparedVolume,
    PreparedVolumeData,
    PreparedVolumeMetadata,
    SpatialAxisUnit,
    TimeAxisUnit,
    TimeTransformation,
)
from cellstar_preprocessor.flows.zarr_methods import open_zarr

# OMEZARR_AXIS_NUMBER_TO_NAME_ORDER = {
#     0:
# }

import dask.array as da

@dataclass
class OMEZarrWrapper:
    path: Path

    # TODO: consider removing original data and downsamplings (if requested)
    # already at this stage 
    # TODO: try to generalize to be able to prepare segmentation data as well
    def prepare_volume_data(self) -> PreparedVolume:
        # Get channel ids here
        # TODO: NOTE that this will add sequential channel ids
        # TO Make them actual ones need mapping
        channel_nums: list[int] = []
        timeframe_indices: list[int] = []
        resolutions: list[int]= []
        l: list[PreparedVolumeData] = []
        omezarr_root = self.get_image_group()
        multiscale = self.get_image_multiscale()
        axes = multiscale.axes    
        for resolution, volume_arr in omezarr_root.arrays():
            # size_of_data_for_lvl = 0
            resolutions.append(resolution)
            if len(axes) == 5 and axes[0].name == AxisName.t:
                for timeframe_index in range(volume_arr.shape[0]):
                    timeframe_indices.append(timeframe_index)
                    for channel_num in range(volume_arr.shape[1]):
                        # from array? 
                        # yes
                        data: da.Array = da.from_zarr(volume_arr)[timeframe_index][channel_num].swapaxes(0, 2)

                        l.append(
                            PreparedVolumeData(
                                timeframe_index=timeframe_index,
                                channel_num=channel_num,
                                data=data,
                                resolution=resolution,
                                nbytes=data.nbytes
                            )
                        )

                        channel_nums.append(channel_num)
                        gc.collect()

            elif len(axes) == 4 and axes[0].name == AxisName.c:
                timeframe_indices.append(0)
                for channel_num in range(volume_arr.shape[0]):
                    data = da.from_zarr(volume_arr)[channel_num].swapaxes(0, 2)
                    l.append(
                            PreparedVolumeData(
                                timeframe_index='0',
                                channel_num=channel_num,
                                data=data,
                                resolution=resolution,
                                nbytes=data.nbytes
                            )
                        )
                    channel_nums.append(channel_num)
                    gc.collect()
            else:
                raise Exception(f"Axes number/order {axes} is not supported")
        
        return PreparedVolume(
            data=l,
            metadata=PreparedVolumeMetadata(
                channel_nums=channel_nums,
                timeframe_indices=timeframe_indices,
                resolutions=resolutions
            )
        )
    
    def get_image_resolutions(self):
        r_str = self.get_image_group().array_keys()
        return sorted([int(r) for r in r_str])

    def get_label_resolutions(self, label_name: str):
        r_str = self.get_labels_group()[label_name].group_keys()
        return sorted([int(r) for r in r_str])

    def get_image_group(self):
        return open_zarr(self.path)

    def get_labels_group(self) -> zarr.Group:
        return self.get_image_group().labels

    def get_label_names(self):
        return list(self.get_labels_group().group_keys())

    def get_image_zattrs(self):
        zattrs = self.get_image_group().attrs
        return OMEZarrAttrs.model_validate(zattrs)

    def get_label_zattrs(self, label_name: str):
        zattrs = self.get_labels_group()[label_name].attrs
        return OMEZarrAttrs.model_validate(zattrs)

    def get_image_multiscale(self):
        """Only the first multiscale"""
        # NOTE: can be multiple multiscales, here picking just 1st
        return self.get_image_zattrs().multiscales[0]

    def get_label_multiscale(self, label_name: str):
        """Only the first multiscale"""
        # NOTE: can be multiple multiscales, here picking just 1st
        return self.get_label_zattrs(label_name).multiscales[0]

    def get_axes(self):
        """Root level axes, not present in majority of used OMEZarrs"""
        raise NotImplementedError()

    def create_channel_ids_mapping(self):
        m: dict[str, str] = {}
        if self.get_omero_channels() is not None:
            # NOTE: order should correspond to order of array
            for idx, channel in enumerate(self.get_omero_channels()):
                channel_id = str(idx) if channel.label is None else channel.label
                m[str(idx)] = channel_id
        else:
            # if not able - create artificial from channel_ids
            # iterate over prepared volume data
            for channel_num in self.prepared.metadata.channel_nums:
                m[str(channel_num)] = str(channel_num) 
                
        return m
        
    
    def get_omero_channels(self):
        # should check if exists, if not - return so
        if self.get_image_zattrs().omero:
            if self.get_image_zattrs().omero.channels: 
                return self.get_image_zattrs().omero.channels
            
        return None

    def get_time_units(self):
        m = self.get_image_multiscale()
        axes = m.axes
        t_axis = axes[0]
        # change to ax
        if t_axis.name == AxisName.t:
            if t_axis.unit is not None:
                return t_axis.unit
        # if first axes is not time
        return TimeAxisUnit.millisecond

    def set_zattrs(self, new_zattrs: dict[str, Any]):
        root = self.get_image_group()
        root.attrs.put(new_zattrs)
        print(f"New zattrs: {root.attrs}")

    def add_defaults_to_ome_zarr_attrs(self):
        zattrs = self.get_image_zattrs()
        axes = zattrs.multiscales[0].axes
        for axis in axes:
            if axis.unit is None:
                # if axis.type is not None:
                if axis.name in [AxisName.x, AxisName.y, AxisName.z]:
                    axis.unit = SpatialAxisUnit.angstrom
                elif axis.name == AxisName.t:
                    axis.unit = TimeAxisUnit.millisecond

        self.set_zattrs(zattrs.model_dump())

    def process_time_transformations(self):
        # NOTE: can be multiple multiscales, here picking just 1st
        time_transformations_list: list[TimeTransformation] = []
        multiscales = self.get_image_multiscale()
        axes = multiscales.axes
        datasets_meta = multiscales.datasets
        first_axis = axes[0]
        if first_axis.name == AxisName.t:
            for idx, level in enumerate(datasets_meta):
                assert (
                    level.coordinateTransformations[0].scale is not None
                ), "OMEZarr should conform to v4 specification with scale"
                scale_arr = level.coordinateTransformations[0].scale
                if len(scale_arr) == 5:
                    factor = scale_arr[0]
                    if multiscales.coordinateTransformations is not None:
                        if multiscales.coordinateTransformations[0].type == "scale":
                            factor = (
                                factor
                                * multiscales.coordinateTransformations[0].scale[0]
                            )
                    time_transformations_list.append(
                        TimeTransformation(downsampling_level=level.path, factor=factor)
                    )
                else:
                    raise Exception("Length of scale arr is not supported")

            return time_transformations_list
        else:
            return time_transformations_list
