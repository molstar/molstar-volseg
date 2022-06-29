

from pathlib import Path


def write_dict_to_txt(d: dict, filename: Path):
    with filename.open('w') as fp:
        lst = [f'{k}: {str(v)}\n' for k, v in d.items()]
        fp.writelines(lst)