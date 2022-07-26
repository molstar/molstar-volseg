from pathlib import Path
import zarr

def open_zarr_zip(path: Path) -> zarr.hierarchy.Group:
    store = zarr.ZipStore(
        path=path,
        compression=0,
        allowZip64=True,
        mode='r'
    )
    # Re-create zarr hierarchy from opened store
    root: zarr.hierarchy.group = zarr.group(store=store)
    return root