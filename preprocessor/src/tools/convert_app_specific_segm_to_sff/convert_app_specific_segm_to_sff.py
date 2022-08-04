from pathlib import Path
from sfftk.formats.am import AmiraMeshSegmentation
from sfftk.formats.mod import IMODSegmentation
from sfftk.formats.seg import SeggerSegmentation
from sfftk.formats.stl import STLSegmentation
from sfftk.formats.surf import AmiraHyperSurfaceSegmentation

def convert_app_specific_segm_to_sff(input_file: Path) -> Path:
    '''Converts application specific segmentation to SFF (.hff)'''
    extension = input_file.suffix
    filepath_str = str(input_file.resolve())
    if extension == '.am':
        app_spec_seg = AmiraMeshSegmentation(filepath_str)
    elif extension == '.mod': 
        app_spec_seg = IMODSegmentation(filepath_str)
    elif extension == '.seg':   
        app_spec_seg = SeggerSegmentation(filepath_str)
    elif extension == '.stl':    
        app_spec_seg = STLSegmentation(filepath_str)
    elif extension == '.surf':    
        app_spec_seg = AmiraHyperSurfaceSegmentation(filepath_str)
    else:
        raise Exception('application specific segmentation file extension is not supported')

    sff_seg = app_spec_seg.convert()