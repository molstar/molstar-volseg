from pathlib import Path
import mrcfile
from preprocessor.src.preprocessors.implementations.sff.preprocessor.constants import DOWNSAMPLING_KERNEL
from scipy import signal, ndimage
import numpy as np
from preprocessor.src.preprocessors.implementations.sff.preprocessor.downsampling.downsampling import generate_kernel_3d_arr
from timeit import default_timer as timer

def downsample_map(input_path: Path, output_path: Path, size_limit: int):
    # use read function






def _delete():


    INPUT_MAP = 'preprocessor\data\sample_volumes\emdb_sff\emd_9199.map'
    # INPUT_MAP = 'preprocessor\data\sample_volumes\emdb_sff\EMD-1832.map'
    OUTPUT_MAP = 'temp/downsampled_9199.map'

    kernel = generate_kernel_3d_arr(list(DOWNSAMPLING_KERNEL))

    data_to_write = None

    start_mrcfile = timer()
    with mrcfile.open(INPUT_MAP) as mrc:
        stop_mrcfile = timer()
        start_data = timer()
        data = mrc.data
        stop_data = timer()
        # works with 16GB RAM
        # print(data.shape)

        # works
        start_convolve = timer()
        downsampled_data = ndimage.convolve(data, kernel, mode='mirror', cval=0.0)
        stop_convolve = timer()

        downsampled_data = downsampled_data[::2, ::2, ::2]
        stop_every_other = timer()
        # print(downsampled_data.shape)

        print(f'mrcfile opening took: {stop_mrcfile - start_mrcfile}')
        print(f'accessing mrc object data (numpy arr) took: {stop_data - start_data}')
        print(f'convolve took: {stop_convolve - start_convolve}')
        print(f'slicing (every other value) took: {stop_every_other - stop_convolve}')

        data_to_write = downsampled_data

    with mrcfile.new(OUTPUT_MAP, overwrite=True) as mrc:
        set_data_start = timer()
        mrc.set_data(data_to_write)
        set_data_stop = timer()
        print(f'writing data to new file took: {set_data_stop - set_data_start}')


    with mrcfile.open(OUTPUT_MAP) as mrc:
        data = mrc.data
        print(f'shape of new file is {data.shape}')
        
        # other options:
        # open with mmap
        # explicitly try specifying 'r' mode while opening