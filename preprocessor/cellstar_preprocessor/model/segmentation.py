from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, Union

from cellstar_db.models import DownsamplingParams, InputKind, SegmentationExtraData, SegmentationPrimaryDescriptor
from cellstar_db.models import EntryData
from cellstar_preprocessor.model.common import InternalData

@dataclass
class InternalSegmentation(InternalData):
    custom_data: SegmentationExtraData | None = None
    primary_descriptor: SegmentationPrimaryDescriptor | None = None
    value_to_segment_id_dict: dict = field(default_factory=dict)
    simplification_curve: dict[int, float] = field(default_factory=dict)
    raw_sff_annotations: dict[str, Any] = field(default_factory=object)
    map_headers: dict[str, object] = field(default_factory=dict)