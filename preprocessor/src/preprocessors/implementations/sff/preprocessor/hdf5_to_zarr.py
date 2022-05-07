def hdf5_to_zarr(self, file_path: Path):
    '''
    Creates temp zarr structure mirroring that of hdf5
    '''
    self.temp_zarr_structure_path = self.temp_root_path / file_path.stem
    store: zarr.storage.DirectoryStore = zarr.DirectoryStore(str(self.temp_zarr_structure_path))
    # directory store does not need to be closed, zip does

    hdf5_file: h5py.File = h5py.File(file_path, mode='r')
    hdf5_file.visititems(__visitor_function)
    hdf5_file.close()

def __visitor_function(self, name: str, node: h5py.Dataset) -> None:
    '''
    Helper function used to create zarr hierarchy based on hdf5 hierarchy from sff file
    Takes nodes one by one and depending of their nature (group/object dataset/non-object dataset)
    creates the corresponding zarr hierarchy element (group/array)
    '''
    # input hdf5 file may be too large for memory, so we save it in temp storage
    node_name = node.name[1:]
    if isinstance(node, h5py.Dataset):
        # for text-based fields, including lattice data (as it is b64 encoded zlib-zipped sequence)
        if node.dtype == 'object':
            data = [node[()]]
            arr = zarr.array(data, dtype=node.dtype, object_codec=numcodecs.MsgPack())
            zarr.save_array(self.temp_zarr_structure_path / node_name, arr, object_codec=numcodecs.MsgPack())
        else:
            arr = zarr.open_array(self.temp_zarr_structure_path / node_name, mode='w', shape=node.shape, dtype=node.dtype)
            arr[...] = node[()]
    else:
        # node is a group
        zarr.open_group(self.temp_zarr_structure_path / node_name, mode='w')