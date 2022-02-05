import h5py
import json
import zarr
import sfftkrw as sff
import numpy as np
import numcodecs
# import msgpack
from sys import stdout
import base64
import zlib
# better version of downsampling: skimage.measure.block_reduce
# https://scikit-image.org/docs/dev/api/skimage.measure.html#skimage.measure.block_reduce
# careful with func - it should not be np.mean, as it is segmentation
# (e.g. can have 5-6 segments ike 104, 85... in segment_list), perhaps np.max (kinda every other value)
from skimage.measure import block_reduce

PATH_TO_SEG_DIR = ('./sample_segmentations/emdb_sff/')
PATH_TO_OUTPUT_DIR = ('./output_internal_zarr/')
DOWNSAMPLING_STEPS = 4

# TODO: blosc can replace zlib for better speed: http://python-blosc.blosc.org/tutorial.html 
def decompress_lattice_data(compressed_b64_encoded_data, mode, shape):
    '''
    decodes base64 encoded zlib-zipped byte sequence (lattice data)
    into numpy array that is equal to .data_array of SFFLattice class in sfftkrw

    Examples
    -------
    lat = zarr_structure.lattice_list[0]
    data = decompress_lattice_data(lat.data[0], lat.mode[0], (lat.size.cols[...], lat.size.rows[...], lat.size.sections[...]))
    '''
    decoded = base64.b64decode(compressed_b64_encoded_data)
    decompressed_bytes = zlib.decompress(decoded)
    raw_arr = np.frombuffer(decompressed_bytes, dtype=mode)
    arr = raw_arr.reshape(shape)
    return arr

# TODO: don't forget to close it or open with "with"
hdf5_file = h5py.File(PATH_TO_SEG_DIR + 'emd_1832.hff', mode='r')
zarr.tree(hdf5_file)
# dest = zarr.open_group('full_hdf5.zarr', mode='w')
# zarr.copy_all(hdf5_file, dest, log=stdout)
# zarr.copy(hdf5_file['global_external_references'], dest, log=stdout)

# TODO: potentially may be rewritten using root.create_group/ group.create_array etc. to get rid of paths
def visitor_func(name, node):
    emdb_seg_id = hdf5_file.filename.split('/')[-1].split('.')[0]
    root_path = PATH_TO_OUTPUT_DIR + emdb_seg_id
    if isinstance(node, h5py.Dataset):
        # for text-based fields, including lattice data (as it is b64 encoded zlib-zipped sequence)
        if node.dtype == 'object':
            # Opt 1
            # arr = zarr.open_array(root_path + node.name, mode='w', shape=node.shape, dtype=node.dtype, object_codec=numcodecs.MsgPack())
            # arr[...] = node[()]
            
            # Opt 2 - works, data is like [[b'Drosophila.....']], so for access use [0]
            data = [node[()]]
            arr = zarr.array(data, dtype=node.dtype, object_codec=numcodecs.MsgPack())
            zarr.save_array(root_path + node.name, arr, object_codec=numcodecs.MsgPack())
        else:
            arr = zarr.open_array(root_path + node.name, mode='w', shape=node.shape, dtype=node.dtype)
            arr[...] = node[()]
            # print(arr)
    else:
        # node is a group
        # TODO: fix paths
        zarr.open_group(root_path + node.name, mode='w')

# HDF5 => Zarr structure conversion
hdf5_file.visititems(visitor_func)
hdf5_file.close()

# Downsampling step
zarr_structure = zarr.open_group(PATH_TO_OUTPUT_DIR + 'emd_1832')
for gr_name, gr in zarr_structure.lattice_list.groups():
    data = decompress_lattice_data(
        gr.data[0],
        gr.mode[0],
        (gr.size.cols[...], gr.size.rows[...], gr.size.sections[...]))

    downsampled_data_group = gr.create_group('downsampled_data')
    # iteratively downsample data, create arr for each dwns. level and store data 
    ratios = 2 ** np.arange(1, DOWNSAMPLING_STEPS + 1)
    for rate in ratios:
        data = block_reduce(data, block_size=(2, 2, 2), func=np.max)
        downsampled_data_arr = downsampled_data_group.create_dataset(
            str(rate),
            shape=data.shape,
            dtype=data.dtype)
        downsampled_data_arr[...] = data
    # TODO: figure out compression/filters: b64 encoded zlib-zipped .data is just 8 bytes, downsamplings
    # in raw uncompressed state are much more
    # TODO: figure out also chunks - currently they are not used

# Storing as a file (ZIP, bzip2 compression)
# Compression constants for compression arg of ZipStore()
# ZIP_STORED = 0
# ZIP_DEFLATED = 8 (zlip)
# ZIP_BZIP2 = 12
# ZIP_LZMA = 14
# close store after writing! or use 'with' https://zarr.readthedocs.io/en/stable/api/storage.html#zarr.storage.ZipStore
store = zarr.ZipStore(PATH_TO_OUTPUT_DIR + 'emd_1832.zip', mode='w', compression=12)
zarr.copy_store(zarr_structure.store, store)
store.close()

# print(zarr_structure.tree())
# print(zarr_structure['details'][()])



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
