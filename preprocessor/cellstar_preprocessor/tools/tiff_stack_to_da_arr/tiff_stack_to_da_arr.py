# import os 
# from PIL import Image
# import numpy as np


# import gc
# from pyometiff import OMETIFFReader
from pathlib import Path
# import dask.array as da
# from skimage.io import imread
from dask.array.image import imread

# Image.MAX_IMAGE_PIXELS = None

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
    im = imread(str((dir_path / '*.tiff').resolve()))  
    # print(im.shape)
    return im

# if __name__ == '__main__':
#     p = Path('/mnt/data_backup_ceph/datasets_from_alessio/empiar-12017/WT_fed_6461_mitochondria_instance_segmentation')
#     tiff_to_da_arr(p)