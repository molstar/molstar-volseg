# import os 
# from PIL import Image
# import numpy as np
import multiprocessing
from cellstar_preprocessor.flows.constants import DOWNSAMPLING_KERNEL
from cellstar_preprocessor.flows.volume.helper_methods import generate_kernel_3d_arr
from dask_image.ndfilters import convolve as dask_convolve

# import gc
# from pyometiff import OMETIFFReader
from pathlib import Path
# import dask.array as da
# from skimage.io import imread
import dask.array as da
from dask.array.image import imread as imread_array
from dask_image.imread import imread as imread_image
import tifffile
# Image.MAX_IMAGE_PIXELS = None

# TODO: add package to env

import sys
import pyvips

def _downsize_tiff(p: Path, output: Path, factor: int):
    original_image = pyvips.Image.new_from_file(str(p.resolve()))
    new_w = int(original_image.width / factor)
    new_h = int(original_image.height / factor)
    t = pyvips.Image.thumbnail(str(p.resolve()), new_w, height=new_h)

    # Save with LZW compression
    t.tiffsave(str(output.resolve()), tile=True, compression='lzw')
    return output


# try this as well
def _join_tiff_stack(tiff_filenames: list[Path], output_tiff: Path):
    images = [pyvips.Image.new_from_file(str(f.resolve()), access="sequential")
            for f in tiff_filenames]
    # TODO: accross?
    final: pyvips.Image = pyvips.Image.arrayjoin(images)
    final.write_to_file(str(output_tiff.resolve()))

def _force_downsample_data(data: da.Array, downsampling_steps: int):
    kernel = generate_kernel_3d_arr(list(DOWNSAMPLING_KERNEL))
    current_level_data = data
    for i in range(downsampling_steps):
        current_ratio = 2 ** (i + 1)
        downsampled_data = dask_convolve(
                        current_level_data, kernel, mode="mirror", cval=0.0
                    )
        downsampled_data = downsampled_data[::2, ::2, ::2]
        current_level_data = downsampled_data
    
    print(f"current_ratio: {current_ratio}")
    return downsampled_data

def tiff_stack_to_da_arr(dir_path: Path):
    # NOTE: Approach 1: probably working
    # final = []
    # dirname = str(dir_path.resolve())
    # for fname in os.listdir(dirname):
    #     im = Image.open(os.path.join(dirname, fname))
    #     imarray = np.array(im)
    #     final.append(imarray)

    # final = np.asarray(final)
    
    # img_array = da.from_array(final)
    # del final
    # gc.collect()
    # print(img_array.shape)
    # return img_array

    # NOTE: Approach 2: works
    # TODO: .tif too
    
    # TODO: Lazily load images with Dask Array
    # tifffile.memmap
    
    
    # im = imread_array(str(dir_path.resolve()) + '/' + '*.tiff')  
    # first downsample tiffs then read them here
    
    # iterate over tiffs in dir
    factor = 8
    # do in parallel, do not need to collect pathes
    original_pathes = dir_path.glob('*.tiff')
    original_pathes = [p for p in original_pathes if '_downsized' not in p.stem]
    pathes = [(t, t.with_stem(t.stem + '_downsized'), factor) for t in original_pathes]
    with multiprocessing.Pool(multiprocessing.cpu_count()) as p:
        p.starmap(_downsize_tiff, pathes)

    p.join()
    # for t in dir_path.glob('*.tiff'):
    #     d = _downsize_tiff(t, t.with_stem(t.stem + '_downsized'))
    #     downsized.append(d)
    
    # TODO: problem may be with reading, may need to construct glob pattern properly
    im = imread_array(str((dir_path / '*_downsized.tiff').resolve()))
    # im = imread_array(str((dir_path / '*.tiff').resolve()))
    # downsampled = _force_downsample_data(im, 8)
    # im = imread_image(str((dir_path / '*.tiff').resolve()))
    # this is string
    # _join_tiff_stack(str((dir_path / '*.tiff').resolve()),  str((dir_path / 'VOLUME.tiff').resolve()))
    # print(im.shape)
    # return downsampled
    return im

if __name__ == '__main__':
    p = Path('/mnt/data_backup_ceph/datasets_from_alessio/empiar-12017/WT_fed_6461_mitochondria_instance_segmentation')
    # p = Path('preprocessor/cellstar_preprocessor/tools/tiff_stack_to_da_arr')
    tiff_stack_to_da_arr(p)