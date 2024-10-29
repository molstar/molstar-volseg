from argparse import Namespace
from pathlib import Path

from sfftk.formats.am import AmiraMeshSegmentation
from sfftk.formats.mod import IMODSegmentation
from sfftk.formats.seg import SeggerSegmentation
from sfftk.formats.stl import STLSegmentation
from sfftk.formats.surf import AmiraHyperSurfaceSegmentation


def convert_app_specific_segm_to_sff(input_file: Path) -> Path:
    """Converts application specific segmentation to SFF (.hff)"""
    extension = input_file.suffix
    filepath_str = str(input_file.resolve())
    sff_filepath_str = str((input_file.with_suffix(".hff")).resolve())
    if extension == ".am":
        app_spec_seg = AmiraMeshSegmentation(filepath_str)
    elif extension == ".mod":
        app_spec_seg = IMODSegmentation(filepath_str)
    elif extension == ".seg":
        app_spec_seg = SeggerSegmentation(filepath_str)
    elif extension == ".stl":
        # temp fix from Paul Korir
        app_spec_seg = STLSegmentation([filepath_str])
    elif extension == ".surf":
        # won't work because of sfftk bug https://github.com/emdb-empiar/sfftk/issues/25
        app_spec_seg = AmiraHyperSurfaceSegmentation(filepath_str)
    else:
        raise Exception(
            f"application specific segmentation file extension {extension} is not supported"
        )

    # temp fix from Paul Korir
    # args = Namespace()
    # args.details = None
    # args.verbose = None

    sff_seg = app_spec_seg.convert()
    try:
        sff_seg.export(fn=sff_filepath_str)
    except AttributeError:
        pass

    return Path(sff_filepath_str)


if __name__ == "__main__":
    convert_app_specific_segm_to_sff(Path('preprocessor/temp/working_folder/tubulin.stl'))