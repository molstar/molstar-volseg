

import base64
import logging
from cellstar_preprocessor.flows.common import decide_np_dtype
import numpy as np
import dask.array as da

def decode_base64_data(data: str, mode: str, endianness: str):
    try:
        # TODO: decode any data, take into account endiannes
        decoded_data = base64.b64decode(data)
        np_dtype = decide_np_dtype(mode=mode, endianness=endianness)
        arr = np.frombuffer(decoded_data, dtype=np_dtype)
    except Exception as e:
        logging.error(e, stack_info=True, exc_info=True)
        raise e
    return da.from_array(arr)
