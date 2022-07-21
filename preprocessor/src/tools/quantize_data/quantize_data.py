
from pathlib import Path
from typing import Union
import mrcfile
import numpy as np
import dask.array as da

def read_ccp4_map_mrcfile(map_path: Path) -> np.ndarray:
    with mrcfile.mmap(str(map_path.resolve())) as mrc_original:
        data: np.memmap = mrc_original.data
    return data

def quantize_data(data: Union[da.Array, np.ndarray], output_dtype) -> dict:
    bits_in_dtype = output_dtype().itemsize * 8
    num_steps = 2**bits_in_dtype - 1
    src_data_type = data.dtype.str
    original_min = data.min()
    added_to_remove_negatives = da.absolute(original_min) + 1

    # remove negatives
    da.subtract(data, original_min - 1, out=data)
    # log transform
    data = da.log(data)

    max_value = data.max()
    min_value = data.min()

    delta = (max_value - min_value) / (num_steps - 1)

    quantized = da.subtract(data, min_value)
    da.divide(quantized, delta, out=quantized)
    if isinstance(quantized, da.Array):
        quantized = da.round(quantized, 0)
    elif isinstance(quantized, np.ndarray):
        np.round(quantized, 0, out=quantized)
    else:
        raise Exception('array dtype is neither dask arr nor np ndarray')
    quantized = quantized.astype(dtype=output_dtype)

    # if isinstance(data, da.Array):
    #     quantized = quantized.compute()
    
    d = {
        "min": min_value,
        "max": max_value,
        "num_steps": num_steps,
        "src_type": src_data_type,
        "data": quantized,
        "added_to_remove_negatives": added_to_remove_negatives,
    }

    return d

def decode_quantized_data(data_dict: dict) -> Union[da.Array, np.ndarray]:
    # this will decode back to log data
    delta = (data_dict["max"] - data_dict["min"]) / (data_dict["num_steps"] - 1)
    log_data = data_dict["data"].astype(dtype=data_dict["src_type"])
    da.multiply(log_data, delta, out=log_data)
    da.add(log_data, data_dict["min"], out=log_data)

    original_data = da.exp(log_data)
    da.subtract(original_data, data_dict["added_to_remove_negatives"], out=original_data)

    return original_data

if __name__ == '__main__':
    INPUT_MAP_PATH = Path('preprocessor\data\sample_volumes\emdb_sff\EMD-1832.map')
    # INPUT_MAP_PATH = Path('preprocessor\data\sample_volumes\emdb_sff\emd_9199.map')
    data = read_ccp4_map_mrcfile(INPUT_MAP_PATH)
    data = da.from_array(data)
    quantized_data = quantize_data(data=data, output_dtype=np.uint8)
    print(quantized_data)
