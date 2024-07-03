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

def tiff_stack_to_da_arr(dir_path: Path):
    # TODO: tiff / tif
    im = imread_array(str((dir_path / '*.ti*').resolve()))
    return im