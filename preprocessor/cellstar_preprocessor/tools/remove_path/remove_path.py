
from pathlib import Path
import shutil


def remove_path(path: Path):
    assert path.exists(), f'Path {path} does not exist'
    if path.is_dir():
        shutil.rmtree(path, ignore_errors=True)
    elif path.is_file():
        path.unlink()
    else:
        raise Exception(f'Path type is not recognized for {path}')
        