from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import matplotlib as mpl
from mpl_toolkits.mplot3d import Axes3D
from itertools import product

from preprocessor.implementations.sff_preprocessor import open_zarr_structure_from_path

def plot_3d_array_grayscale(arr: np.ndarray, arr_name: str):
    # source: https://stackoverflow.com/questions/45969974/what-is-the-most-efficient-way-to-plot-3d-array-in-python
    # TODO: fix grayscale - should be 0 to 1
    volume = arr

    # Create the x, y, and z coordinate arrays.  We use 
    # numpy's broadcasting to do all the hard work for us.
    # We could shorten this even more by using np.meshgrid.
    x = np.arange(volume.shape[0])[:, None, None]
    y = np.arange(volume.shape[1])[None, :, None]
    z = np.arange(volume.shape[2])[None, None, :]
    x, y, z = np.broadcast_arrays(x, y, z)

    # Turn the volumetric data into an RGB array that's
    # just grayscale.  There might be better ways to make
    # ax.scatter happy.
    c = np.tile(volume.ravel()[:, None], [1, 3])

    # Do the plotting in a single call.
    fig = plt.figure()
    ax = fig.gca(projection='3d')
    ax.scatter(x.ravel(),
            y.ravel(),
            z.ravel(),
            c=c)

    plt.show()
    plt.savefig(f'{arr_name}.png')

def plot_3d_array_color(arr: np.ndarray, arr_name: str):
    # source: https://stackoverflow.com/questions/45969974/what-is-the-most-efficient-way-to-plot-3d-array-in-python
    shape = arr.shape
    fig = plt.figure(figsize=(10,10))
    ax = fig.add_subplot(projection="3d")
    space = np.array([*product(range(shape[0]), range(shape[1]), range(shape[2]))]) # all possible triplets of numbers from 0 to N-1
    volume = arr
    ax.scatter(space[:,0], space[:,1], space[:,2], c=space/max(shape), s=volume*100)
    # plt.show()
    plt.savefig(Path(f'preprocessor/sample_arr_plots/{arr_name}.png'))

def plot_all_volume_data(volume_data):
    for arr_name, arr in volume_data.arrays():
        print(arr_name)
        print(arr[...])
    # without it, there still would be a plot, but some runtime error related to sqrt from negative
        negative_to_zero = arr[...].clip(min=0)
    
    # plot_3d_array_grayscale(arr[...], arr_name)
        plot_3d_array_color(negative_to_zero, arr_name)

def print_segm_values_as_freq_table(arr: np.ndarray):
    # non_zero_ind = arr.nonzero()
    # non_zero_values = arr[non_zero_ind]
    unique, counts = np.unique(arr, return_counts=True)
    print(np.asarray((unique, counts)).T)

def print_all_segm_data(segm_data):
    for gr_name, gr in segm_data.groups():
        print(f'Lattice #{gr_name}')  
        for dwns_lvl_name, dwns_lvl_gr in gr.groups():
            print(f'Downsampling level x{dwns_lvl_name}')
            print_segm_values_as_freq_table(dwns_lvl_gr.grid[...])


PATH_TO_SAMPLE_SEGMENTATION = Path('db\emdb\emd-1832')

root = open_zarr_structure_from_path(PATH_TO_SAMPLE_SEGMENTATION)
volume_data = root._volume_data
segm_data = root._segmentation_data

plot_all_volume_data(volume_data)

print_all_segm_data(segm_data)



