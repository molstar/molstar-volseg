from typing import Callable, Optional, Union

import numpy as np
from ciftools.binary.encoding.impl.binary_cif_encoder import BinaryCIFEncoder
from ciftools.cif_format import ValuePresenceEnum
from ciftools.writer.base import FieldDesc
from ciftools.writer.fields import number_field


class Fields_SegmentationDataTable:
    def __init__(self, encoder: BinaryCIFEncoder, dtype: np.dtype):
        self.fields: list[FieldDesc] = [
            number_field(name="set_id", value=lambda d, i: d["set_id"][i], dtype=dtype, encoder=lambda d: encoder),
            number_field(name="segment_id", value=lambda d, i: d["segment_id"][i], dtype=dtype, encoder=lambda d: encoder),
        ]
