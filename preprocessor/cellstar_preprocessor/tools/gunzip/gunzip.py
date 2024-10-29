import gzip
import shutil
from pathlib import Path


def gunzip(i: Path, o: Path, remove_gz: bool = False):
    with gzip.open(i, "rb") as f_in:
        # bytes?
        # NOTE: only map gz is supported, therefore bytes
        with open(o, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)

    if remove_gz:
        i.unlink()

    return o
