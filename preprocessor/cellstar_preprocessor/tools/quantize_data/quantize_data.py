from pathlib import Path
from typing import Union

from cellstar_db.models import QuantizationInfo
import dask.array as da
import mrcfile
import numpy as np


def read_ccp4_map_mrcfile(map_path: Path) -> np.ndarray:
    with mrcfile.mmap(str(map_path.resolve())) as mrc_original:
        data: np.memmap = mrc_original.data
    return data


def _convert_data_dict_to_python_dtypes(data_dict: dict) -> dict:
    for key in data_dict:
        if key != "data" and (
            isinstance(data_dict[key], da.Array)
            or isinstance(data_dict[key], np.ndarray)
        ):
            if isinstance(data_dict[key], da.Array):
                data_dict[key] = data_dict[key].compute()
            # TODO: check if there is a way to find corresponding dtype for any np float/np (u)int
            if data_dict[key].dtype in (np.float16, np.float32, np.float64):
                data_dict[key] = float(str(data_dict[key]))
            elif data_dict[key].dtype in (
                np.uint8,
                np.uint16,
                np.int8,
                np.int16,
                np.int32,
            ):
                data_dict[key] = int(str(data_dict[key]))
            else:
                raise Exception(
                    f"dtype of quantized data_dict members is {data_dict[key].dtype} and is not supported"
                )

    return data_dict


def quantize_data(
    data: Union[da.Array, np.ndarray], output_dtype: Union[str, type]
) -> dict:

    if isinstance(output_dtype, str):
        output_dtype = np.dtype(output_dtype)
        bits_in_dtype: int = output_dtype.itemsize * 8
    else:
        bits_in_dtype: int = output_dtype().itemsize * 8

    num_steps: int = 2**bits_in_dtype - 1
    src_data_type = data.dtype.str
    original_min = data.min()
    to_remove_negatives = original_min

    # remove negatives
    # here it is subtracting from original downsampled_data if out=downsampled data
    data = da.subtract(data, to_remove_negatives)
    one = np.array([1], dtype=data.dtype)[0]
    data = da.add(data, one)
    # log transform
    data = da.log(data, where=(data != 0))

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
        raise Exception("array dtype is neither dask arr nor np ndarray")
    quantized = quantized.astype(dtype=output_dtype)

    # if isinstance(data, da.Array):
    #     quantized = quantized.compute()

    # convert min_value, max_value, to_remove_negatives to python dtypes
    # if those three are dask arrs, compute() each prior to conversion
    # convert can be done as:
    # 1. x' = str(x)
    # 2. if x.dtype was float32: float(x')
    # if x.dtype was uint8: int(x')

    d = QuantizationInfo(
        
    min=min_value,
        max=max_value,
        num_steps=num_steps,
        src_type=src_data_type,
        data=quantized,
        to_remove_negatives=to_remove_negatives
        )

    d = _convert_data_dict_to_python_dtypes(d)

    return d


def decode_quantized_data(data_dict: dict) -> Union[da.Array, np.ndarray]:
    # this will decode back to log data
    delta = (data_dict["max"] - data_dict["min"]) / (data_dict["num_steps"] - 1)
    log_data = data_dict["data"].astype(dtype=data_dict["src_type"])
    da.multiply(log_data, delta, out=log_data)
    da.add(log_data, data_dict["min"], out=log_data)

    original_data = da.exp(log_data)
    one = np.array([1], dtype=original_data.dtype)[0]
    original_data = da.subtract(original_data, one)
    da.add(original_data, data_dict["to_remove_negatives"], out=original_data)

    return original_data


if __name__ == "__main__":
    INPUT_MAP_PATH = Path("preprocessor\data\sample_volumes\emdb_sff\EMD-1832.map")
    # INPUT_MAP_PATH = Path('preprocessor\data\sample_volumes\emdb_sff\emd_9199.map')
    data = read_ccp4_map_mrcfile(INPUT_MAP_PATH)
    data = da.from_array(data)
    quantized_data = quantize_data(data=data, output_dtype=np.uint8)
    print(quantized_data)
