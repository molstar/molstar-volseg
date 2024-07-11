import dask.array as da
import mrcfile
import numpy as np
import zarr
from cellstar_preprocessor.flows.constants import DEFAULT_CHANNEL_ID, VOLUME_DATA_GROUPNAME
from cellstar_preprocessor.flows.volume.helper_methods import (
    normalize_axis_order_mrcfile,
    store_volume_data_in_zarr,
)
from cellstar_preprocessor.model.volume import InternalVolume


def map_volume_preprocessing(v: InternalVolume):
    """1. normalize axis order
    2. add volume data to intermediate zarr structure
    """
    
    # generalize further
    v.set_custom_data()
    v.prepare()
    v.set_channels_ids_mapping()
    v.postprepare()
    v.store()
    v.remove_original_resolution()
    v.remove_downsamplings()
    
    print("Volume processed")
