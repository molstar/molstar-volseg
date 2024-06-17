from pathlib import Path
from typing import Optional, Union

from cellstar_db.models import SegmentationExtraData
from cellstar_preprocessor.model.input import DownsamplingParams, EntryData


class InternalSegmentation:
    def __init__(
        self,
        intermediate_zarr_structure_path: Path,
        segmentation_input_path: Union[Path, list[Path]],
        params_for_storing: dict,
        downsampling_parameters: DownsamplingParams,
        entry_data: EntryData,
        sphere_radius: Optional[float] = None,
        color: Optional[float] = None,
        pixel_size: Optional[float] = None,
        star_file_coordinate_divisor: Optional[float] = None,
        custom_data: Optional[SegmentationExtraData] = None,
    ):
        self.intermediate_zarr_structure_path = intermediate_zarr_structure_path
        self.segmentation_input_path = segmentation_input_path
        self.params_for_storing = params_for_storing
        self.downsampling_parameters = downsampling_parameters
        self.primary_descriptor = None
        self.value_to_segment_id_dict: dict = {}
        self.simplification_curve: dict[int, float] = {}
        self.entry_data = entry_data
        self.raw_sff_annotations = {}
        self.sphere_radius = sphere_radius
        self.color = color
        self.pixel_size = pixel_size
        self.star_file_coordinate_divisor = star_file_coordinate_divisor
        self.custom_data = custom_data
        self.map_headers: dict[str, object] = {}
