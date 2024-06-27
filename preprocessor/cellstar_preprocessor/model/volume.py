from pathlib import Path
from typing import Optional

from cellstar_db.models import VolumeExtraData
from cellstar_preprocessor.model.input import (
    DownsamplingParams,
    EntryData,
    InputKind,
    QuantizationDtype,
)


class InternalVolume:
    def __init__(
        self,
        intermediate_zarr_structure_path: Path,
        volume_input_path: Path,
        params_for_storing: dict,
        volume_force_dtype: str,
        downsampling_parameters: DownsamplingParams,
        entry_data: EntryData,
        quantize_dtype_str: QuantizationDtype,
        quantize_downsampling_levels: tuple,
        input_kind: InputKind,
        custom_data: Optional[VolumeExtraData] = None
    ):
        self.intermediate_zarr_structure_path = intermediate_zarr_structure_path
        self.volume_input_path = volume_input_path
        self.params_for_storing = params_for_storing
        self.quantize_dtype_str = quantize_dtype_str
        self.volume_force_dtype = volume_force_dtype
        self.downsampling_parameters = downsampling_parameters
        self.entry_data = entry_data
        self.map_header = None
        self.quantize_downsampling_levels = quantize_downsampling_levels
        self.custom_data = custom_data
        self.input_kind = input_kind
