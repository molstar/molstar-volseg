from pathlib import Path
from cellstar_db.models import ConlistFloat3, DataKind, ParsedMap
from cellstar_preprocessor.flows.volume.helper_methods import normalize_axis_order_mrcfile
import mrcfile
import numpy as np
import dask.array as da
# 
def parse_map(i: Path, voxel_size: ConlistFloat3 | None = None, dtype: str | np.dtype | None = None, map_type: DataKind = DataKind.volume ):
    # should yield info sufficient for volume and for segmentation (mask case)
    with mrcfile.mmap(i, "r+") as mrc_original:
        data: np.memmap = mrc_original.data
        if dtype is not None:
            data = data.astype(dtype)
        
        # temp hack to process rec files with cella 0 0 0
        # if mrc_original.header.cella.x == 0 and mrc_original.header.cella.y == 0 and mrc_original.header.cella.z == 0:
        if voxel_size is not None:
            mrc_original.voxel_size = 1 * voxel_size

        header: np.recarray = mrc_original.header
        # single channel and timeframe

        dask_arr = da.from_array(data)
        dask_arr = normalize_axis_order_mrcfile(dask_arr=dask_arr, mrc_header=header)
        
        
        if map_type == DataKind.segmentation:
            # TODO: check if dask_arr has this dtype kind
            if dask_arr.dtype.kind == "f":
                dask_arr.setflags(write=1)
                dask_arr = dask_arr.astype("i4")
                
        return ParsedMap(
            data = dask_arr,
            header = header
        )