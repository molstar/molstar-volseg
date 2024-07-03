# import os
# from PIL import Image
# import numpy as np

# import gc
# from pyometiff import OMETIFFReader
from pathlib import Path

# import dask.array as da
# from skimage.io import imread
from dask.array.image import imread as imread_array


def tiff_stack_to_da_arr(dir_path: Path):
    # TODO: tiff / tif
    im = imread_array(str((dir_path / "*.ti*").resolve()))
    return im
