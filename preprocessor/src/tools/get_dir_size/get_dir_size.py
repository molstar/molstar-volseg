
from pathlib import Path


def get_dir_size(folder: Path):
    '''Directory size in bytes'''
    # stat().st_size - size of file in bytes
    # .rglob - recursive glob
    size = sum(file.stat().st_size for file in folder.rglob('*'))
    return size