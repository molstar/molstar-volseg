


import math
from pathlib import Path
from dask_image.ndfilters import convolve as dask_convolve
import numpy as np
import mrcfile
import dask.array as da

def downsample_map(in_map: Path, out_map: Path, factor: int, kernel: np.ndarray):
    with mrcfile.mmap(
        str(in_map.resolve()), "r+"
    ) as mrc_original:
        current_level_data: np.memmap = mrc_original.data
        current_level_data = da.from_array(current_level_data)
        # kernel = kernel.astype(current_level_data.dtype)
        downsampling_steps = int(math.log2(factor))
        for i in range(downsampling_steps):
            current_ratio = 2 ** (i + 1)
            downsampled_data = dask_convolve(
                current_level_data, kernel, mode="mirror", cval=0.0
            )
            downsampled_data = downsampled_data[::2, ::2, ::2]
            current_level_data = downsampled_data
            
    # write 
    with mrcfile.mmap(
        str(out_map.resolve()), "w+"
    ) as mrc_original:
        mrc_original.set_data(current_level_data)

# check if works  
    
    # return current_level_data