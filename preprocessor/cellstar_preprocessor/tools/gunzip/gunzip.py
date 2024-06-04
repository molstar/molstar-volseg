import gzip
import shutil
from pathlib import Path


def gunzip(gz_path: Path):
    """
    Only maps or sff
    Gunzips to same folder
    Removes gz archieve
    """
    filename = gz_path.name
    gunzipped_filename = gz_path.parent / filename.removesuffix(".gz")
    with gzip.open(str(gz_path.resolve()), "rb") as f_in:
        # bytes?
        # NOTE: only map gz is supported, therefore bytes
        with open(str(gunzipped_filename.resolve()), "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)

    gz_path.unlink()

    return gunzipped_filename
