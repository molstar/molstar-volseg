import zarr
import numpy as np
import dask.array as da

# 1: numpy slicing (currently)
# 

# 2: zarr slicing via : notation
root = zarr.group(store=store)
arr = root.sgroup.sarr
slice = arr[1:3, 1:3, 1:3]

# 3: zarr slicing via get_basic_selection and python slices
root = zarr.group(store=store)
arr = root.sgroup.sarr
slice = arr.get_basic_selection(slice(1, 3), slice(1,3), slice(1,3))

# 4: dask slicing: https://github.com/zarr-developers/zarr-python/issues/478#issuecomment-531148674
# z = ...  # some zarr array
# zd = da.from_array(z)
# y = zd[::10]  # this is like a view - it's a deferred result, not computed until needed
