from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from cellstar_db.models import DownsamplingParams, InputKind, Metadata, QuantizationDtype, SamplingBox, VolumeExtraData
from cellstar_db.models import (
    EntryData,
)
import zarr
from cellstar_preprocessor.flows.zarr_methods import get_downsamplings
from cellstar_preprocessor.flows.constants import QUANTIZATION_DATA_DICT_ATTR_NAME
from cellstar_preprocessor.flows.volume.helper_methods import get_origin_from_map_header, get_voxel_sizes_from_map_header
from cellstar_preprocessor.model.common import InternalData
import dask.array as da
import numpy as np
from cellstar_preprocessor.tools.quantize_data.quantize_data import decode_quantized_data


@dataclass
class InternalVolume(InternalData):
    volume_force_dtype: str
    quantize_dtype_str: QuantizationDtype
    quantize_downsampling_levels: tuple
    custom_data: VolumeExtraData | None = None
    map_header: object | None = None
    
    def get_origin(self):
        kind = self.input_kind
        if kind == InputKind.map:
            return get_origin_from_map_header(self.map_header)
        # elif kind == InputKind.omezarr:
        #     return get_origin_from_omezarr(...)
        # elif kind == InputKind.ometiff_image:
        #     return get_origin_from_ometiff_image(...)
    
    def get_voxel_sizes(self):
        kind = self.input_kind
        if kind == InputKind.map:
            return get_voxel_sizes_from_map_header(self.map_header, get_downsamplings(self.get_volume_data_group()))
        # TODO: other
    
    def get_grid_dimensions(self):
        volume_data_group = self.get_volume_data_group()
        first_resolution = sorted(volume_data_group.group_keys())[0]
        first_time: str = sorted(volume_data_group[first_resolution].array_keys())[0]
        return volume_data_group[first_resolution][first_time].shape
    
    def set_volume_sampling_info(self):
        volume_data_group = self.get_volume_data_group()
        origin = self.get_origin()
        voxel_sizes = self.get_voxel_sizes()
        
        sampling_info_dict = self.get_metadata().volumes.volume_sampling_info
        for res_gr_name, res_gr in volume_data_group.groups():
            # TODO: grid dimensions get
            sampling_info_dict.boxes[res_gr_name] = SamplingBox(
                origin=origin,
                    voxel_size=voxel_sizes[int(res_gr_name)],
                    grid_dimensions=self.get_grid_dimensions()
                )
            #     "origin": origin,
            #     "voxel_size": voxel_sizes[int(res_gr_name)],
            #     "grid_dimensions": self.get_grid_dimensions()
            # }

            sampling_info_dict["descriptive_statistics"][res_gr_name] = {}

            for time_gr_name, time_gr in res_gr.groups():
                first_group_key = sorted(time_gr.array_keys())[0]

                sampling_info_dict["boxes"][res_gr_name]["grid_dimensions"] = time_gr[
                    first_group_key
                ].shape
                # sampling_info_dict['boxes'][res_gr_name]['force_dtype'] = time_gr[first_group_key].dtype.str

                sampling_info_dict["descriptive_statistics"][res_gr_name][time_gr_name] = {}
                for channel_arr_name, channel_arr in time_gr.arrays():
                    assert (
                        sampling_info_dict["boxes"][res_gr_name]["grid_dimensions"]
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

                    sampling_info_dict["descriptive_statistics"][res_gr_name][time_gr_name][
                        channel_arr_name
                    ] = {
                        "mean": mean_val,
                        "std": std_val,
                        "max": max_val,
                        "min": min_val,
                    }
            