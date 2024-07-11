

from pathlib import Path

from cellstar_preprocessor.tools.remove_path.remove_path import remove_path


def clean_dir(path: Path):
   for p in path.glob("**/*"):
       remove_path(p)