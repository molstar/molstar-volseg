from pathlib import Path
import mrcfile
from preprocessor.src.preprocessors.implementations.sff.preprocessor.constants import DOWNSAMPLING_KERNEL
from scipy import signal, ndimage
import numpy as np
from preprocessor.src.preprocessors.implementations.sff.preprocessor.downsampling.downsampling import generate_kernel_3d_arr
from timeit import default_timer as timer

def downsample_map(input_path: Path, output_path: Path, size_limit: int):
    kernel = generate_kernel_3d_arr(list(DOWNSAMPLING_KERNEL))
    
    # open with mmap if too big
    with mrcfile.open(str(input_path.resolve())) as mrc_original:
        original_cella = mrc_original.header.cella
        data: np.ndarray = mrc_original.data

    size = data.nbytes
    print(f'{input_path.name} - size of original data: ~ {size / 1000000} MB')
    downsampled_data = data

    num_steps = 0
    while size > size_limit:
        num_steps = num_steps + 1
        downsampled_data = ndimage.convolve(downsampled_data, kernel, mode='mirror', cval=0.0)
        downsampled_data = downsampled_data[::2, ::2, ::2]
        size = downsampled_data.nbytes
        print(f'downsampled to: {size / 1000000} MB')
        
    with mrcfile.new(str(output_path.resolve()), overwrite=True) as mrc:
        cella_divisor = 2 ** num_steps
        mrc.set_data(downsampled_data)
        mrc.header.cella.x = original_cella.x / cella_divisor
        mrc.header.cella.y = original_cella.y / cella_divisor
        mrc.header.cella.z = original_cella.z / cella_divisor
        
        mrc.print_header()
        mrc.update_header_from_data()
        mrc.update_header_stats()    
        

def _check_if_map_is_ok(map_path: Path):
    with mrcfile.open(str(map_path.resolve())) as mrc:
        data = mrc.data
        print(f'shape of new file is {data.shape}')
        mrc.print_header()


        
if __name__ == '__main__':
    INPUT_MAP = 'preprocessor\data\sample_volumes\emdb_sff\emd_9199.map'
    # INPUT_MAP = 'preprocessor\data\sample_volumes\emdb_sff\EMD-1832.map'
    OUTPUT_MAP = 'temp/downsampled_9199.map'
    SIZE_LIMIT = 1 * (10**9)
    downsample_map(input_path=Path(INPUT_MAP), output_path=Path(OUTPUT_MAP), size_limit=SIZE_LIMIT)
    _check_if_map_is_ok(Path(OUTPUT_MAP))
    
        