import logging
from pathlib import Path

import h5py
import numcodecs
import zarr

temp_zarr_structure_path = None


def hdf5_to_zarr(temp_root_path: Path, file_path: Path, entry_id: str) -> Path:
    '''
    Creates temp zarr structure mirroring that of hdf5
    '''
    global temp_zarr_structure_path
    temp_zarr_structure_path = temp_root_path / entry_id
    try:
        assert temp_zarr_structure_path.exists() == False, \
            f'temp_zarr_structure_path: {temp_zarr_structure_path} already exists'
        store: zarr.storage.DirectoryStore = zarr.DirectoryStore(str(temp_zarr_structure_path))
        # directory store does not need to be closed, zip does
        hdf5_file: h5py.File = h5py.File(file_path, mode='r')
        hdf5_file.visititems(__visitor_function)
        hdf5_file.close()
    except Exception as e:
        logging.error(e, stack_info=True, exc_info=True)
    return temp_zarr_structure_path


def __visitor_function(name: str, node: h5py.Dataset) -> None:
    '''
    Helper function used to create zarr hierarchy based on hdf5 hierarchy from sff file
    Takes nodes one by one and depending of their nature (group/object dataset/non-object dataset)
    creates the corresponding zarr hierarchy element (group/array)
    '''
    global temp_zarr_structure_path
    # input hdf5 file may be too large for memory, so we save it in temp storage
    node_name = node.name[1:]
    if isinstance(node, h5py.Dataset):
        # for text-based fields, including lattice data (as it is b64 encoded zlib-zipped sequence)
        if node.dtype == 'object':
            data = [node[()]]
            arr = zarr.array(data, dtype=node.dtype, object_codec=numcodecs.MsgPack())
            zarr.save_array(temp_zarr_structure_path / node_name, arr, object_codec=numcodecs.MsgPack())
        else:
            arr = zarr.open_array(temp_zarr_structure_path / node_name, mode='w', shape=node.shape,
                                  dtype=node.dtype)
            arr[...] = node[()]
    elif isinstance(node, h5py.Group):
        zarr.open_group(temp_zarr_structure_path / node_name, mode='w')
    else:
        raise Exception('h5py node is neither dataset nor group')
