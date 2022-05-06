def lattice_data_to_np_arr(self, data: str, dtype: str, arr_shape: Tuple[int, int, int]) -> np.ndarray:
    '''
    Converts lattice data to np array.
    Under the hood, decodes lattice data into zlib-zipped data, decompress it to bytes,
    and converts to np arr based on dtype (sff mode) and shape (sff size)
    '''
    decoded_data = base64.b64decode(data)
    byteseq = zlib.decompress(decoded_data)
    # order should be F as frontend requests in X,Y,Z order,
    # while numpy by default has Z,Y,X (C order)
    return np.frombuffer(byteseq, dtype=dtype).reshape(arr_shape, order='F')

def create_value_to_segment_id_mapping(self, zarr_structure):
    '''
    Iterates over zarr structure and returns dict with
    keys=lattice_id, and for each lattice id => keys=grid values, values=segm ids
    '''
    root = zarr_structure
    d = {}
    for segment_name, segment in root.segment_list.groups():
        lat_id = int(segment.three_d_volume.lattice_id[...])
        value = int(segment.three_d_volume.value[...])
        segment_id = int(segment.id[...])
        if lat_id not in d:
            d[lat_id] = {}
        d[lat_id][value] = segment_id
    # print(d)
    return d
