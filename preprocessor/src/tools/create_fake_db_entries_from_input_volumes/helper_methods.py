def _clear_dir_with_files_for_storing(dirpath: Path):
    content = sorted(dirpath.glob('*'))
    for path in content:
        if path.is_file():
            path.unlink()
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)

def convert_map_filename_to_entry_name(map_filename: str) -> str:
    components = re.split('_|-', map_filename.lower())
    entry_name = f'{components[0]}-{components[1]}'
    return entry_name

def get_list_of_input_volume_files(input_volumes_dir: Path) -> List[Path]:
    list_of_input_volumes = []
    contents = sorted(input_volumes_dir.glob('*'))
    for path in contents:
        if path.is_file():
            ext = (path.suffix).lower()
            if ext == '.map' or ext == '.ccp4':
                list_of_input_volumes.append(path)

    return list_of_input_volumes