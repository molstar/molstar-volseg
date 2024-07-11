from decimal import Decimal

import dask.array as da
import numpy as np
from cellstar_db.models import (
    DownsamplingLevelInfo,
    EntryId,
    TimeInfo,
    VolumeSamplingInfo,
    VolumesMetadata,
)
from cellstar_preprocessor.flows.constants import (
    DEFAULT_TIME_UNITS,
    QUANTIZATION_DATA_DICT_ATTR_NAME,
)
from cellstar_preprocessor.flows.volume.helper_methods import (
    _ccp4_words_to_dict_mrcfile,
)
from cellstar_preprocessor.flows.zarr_methods import get_downsamplings
from cellstar_preprocessor.model.volume import InternalVolume
from cellstar_preprocessor.tools.quantize_data.quantize_data import (
    decode_quantized_data,
)

def map_volume_annotations_preprocessing(v: InternalVolume):
    a = v.get_annotations()
    v.set_entry_id_in_annotations()
    a.volume_channels_annotations = v.set_volume_channel_annotations()
