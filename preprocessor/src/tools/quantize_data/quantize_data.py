
from pathlib import Path
import mrcfile
import numpy as np
import dask.array as da

def read_ccp4_map_mrcfile(map_path: Path) -> np.ndarray:
    return mrcfile.read(str(map_path.resolve()))

def quantize_data(data: da.Array, output_dtype) -> np.ndarray:
    bits_in_dtype = output_dtype().itemsize * 8
    num_steps = 2**bits_in_dtype - 1
    
    # remove negatives: add abs min + 1
    np.add(data, np.abs(data.min() + 1), out=data)
    # log transform
    data = np.log(data)

    max_value = data.max()
    min_value = data.min()

    delta = (max_value - min_value) / (num_steps - 1)

    quantized = np.subtract(data, min_value)
    np.divide(quantized, delta, out=quantized)
    quantized = quantized.astype(dtype=output_dtype)

    return quantized.compute()

if __name__ == '__main__':
    INPUT_MAP_PATH = Path('preprocessor\data\sample_volumes\emdb_sff\EMD-1832.map')
    data = read_ccp4_map_mrcfile(INPUT_MAP_PATH)
    data = da.from_array(data)
    quantized_data = quantize_data(data=data, output_dtype=np.uint8)
    print(quantized_data)
