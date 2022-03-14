import zarr
from preprocessor import decompress_lattice_data

PATH_TO_SEG_DIR = ('./sample_segmentations/emdb_sff/')
PATH_TO_OUTPUT_DIR = ('./output_internal_zarr/')

# Open already created store with internal zarr
store = zarr.DirectoryStore(PATH_TO_OUTPUT_DIR + 'emd_1832')
# Re-create zarr hierarchy from opened store
root = zarr.group(store=store)
# Print out some data
print(root.details[...])

latlist = root.lattice_list.groups()
for gr_name, gr in latlist:
    data = decompress_lattice_data(
        gr.data[0],
        gr.mode[0],
        (gr.size.cols[...], gr.size.rows[...], gr.size.sections[...]))
    # Original lattice data as np arr (not downsampled)
    print('Lattice data in original resolution:')
    print(data)

    for arr_name, arr in gr.downsampled_data.arrays():
        print(f'Downsampled data by the factor of {arr_name}')
        print(arr[...])

store.close()