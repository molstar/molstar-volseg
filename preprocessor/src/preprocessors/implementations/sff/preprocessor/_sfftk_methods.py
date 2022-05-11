from pathlib import Path

from sfftkrw.schema.adapter_v0_8_0_dev1 import SFFSegmentation


# TODO: check if the correct adapter is used (0.8.0 or 0.7.0)
def open_hdf5_as_segmentation_object(file_path: Path) -> SFFSegmentation:
    return SFFSegmentation.from_file(str(file_path.resolve()))
