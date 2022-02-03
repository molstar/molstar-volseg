import h5py
import json
import zarr
import sfftkrw as sff
import numpy as np
import numcodecs
import msgpack
from sys import stdout

PATH_TO_SEG_DIR = ('./sample_segmentations/emdb_sff/')
PATH_TO_OUTPUT_DIR = ('./output_internal_zarr/')

# TODO: don't forget to close it or open with "with"
hdf5_file = h5py.File(PATH_TO_SEG_DIR + 'emd_1832.hff', mode='r')
zarr.tree(hdf5_file)
# dest = zarr.open_group('full_hdf5.zarr', mode='w')
# zarr.copy_all(hdf5_file, dest, log=stdout)
# zarr.copy(hdf5_file['global_external_references'], dest, log=stdout)

d = {}
def visitor_func(name, node):
    if isinstance(node, h5py.Dataset):
        if node.dtype in d.keys():     
            d[node.dtype] = d[node.dtype] + 1
        else:
            d[node.dtype] = 1

        # print(node.name)
    else:
        print(node.name)
        # TODO: fix paths
        zarr.open(PATH_TO_OUTPUT_DIR + hdf5_file.filename.split('/')[-1].split('.')[0] + node.name, mode='w')
        # print(node.name)
        # node is a group

hdf5_file.visititems(visitor_func)
# print(hdf5_file.filename)

hdf5_file.close()
# print(d)

# TODO: fix path so that it is working irrespectively of where you call script from
# pathToASegmentation = ("./sample_segmentations/emdb_sff/emd_1832.sff")

# # read from a file
# seg = sff.SFFSegmentation.from_file(pathToASegmentation)

# print(json.dumps(seg.as_json(), indent=4))
# print(seg.details)
# data_arr = seg.lattice_list[0].data_array
# non_zero_indices = np.nonzero(data_arr)
# non_zero_values = data_arr[non_zero_indices]
# # print(non_zero_values)

# create hdf5 file to later add seg.as_hff as hdf5 group to that file
# TODO: fix file paths
# hdf5_file = h5py.File('example.h5', mode='w')
# # hdf5_group = hdf5_file.create_group('example_segmentation')
# # print(zarr.tree(hdf5_file))

# # convert seg to hff group in new hdf5 file
# new_hdf5_file = seg.as_hff(hdf5_file)
# # print(new_hdf5_file)
# # print(zarr.tree(new_hdf5_file))

# # copy from hdf5 group to .zarr group
# dest = zarr.open_group('example2.zarr', mode='w')
# # zarr.copy_all(new_hdf5_file, dest, log=stdout)
# print(dest.tree())
