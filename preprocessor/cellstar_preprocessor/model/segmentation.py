from pathlib import Path
from typing import Optional, Union

from cellstar_db.models import DownsamplingParams, InputKind, SegmentationExtraData
from cellstar_db.models import EntryData


class InternalSegmentation:
    def __init__(
        self,
        intermediate_zarr_structure_path: Path,
        input_path: Union[Path, list[Path]],
        params_for_storing: dict,
        downsampling_parameters: DownsamplingParams,
        entry_data: EntryData,
        input_kind: InputKind,
        sphere_radius: Optional[float] = None,
        color: Optional[float] = None,
        pixel_size: Optional[float] = None,
        star_file_coordinate_divisor: Optional[float] = None,
        custom_data: Optional[SegmentationExtraData] = None,
    ):
        self.intermediate_zarr_structure_path = intermediate_zarr_structure_path
        self.input_path = input_path
        self.params_for_storing = params_for_storing
        self.downsampling_parameters = downsampling_parameters
        self.primary_descriptor = None
        self.value_to_segment_id_dict: dict = {}
        self.simplification_curve: dict[int, float] = {}
        self.entry_data = entry_data
        self.raw_sff_annotations = {}
        self.custom_data = custom_data
        self.map_headers: dict[str, object] = dict()
        self.input_kind = input_kind
