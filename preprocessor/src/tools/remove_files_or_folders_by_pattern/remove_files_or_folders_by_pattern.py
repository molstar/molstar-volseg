from glob import glob
from pathlib import Path
import shutil


def remove_files_or_folders_by_pattern(pattern: str):
    '''Add / at the end if dir'''
    str_paths = glob(pattern)
    paths = [Path(str_path) for str_path in str_paths]
    [shutil.rmtree(path) for path in paths]

if __name__ == '__main__':
    remove_files_or_folders_by_pattern('bb_*/')