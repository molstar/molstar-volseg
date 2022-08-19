
from pathlib import Path
from preprocessor.src.preprocessors.implementations.sff.preprocessor._sfftk_methods import open_hdf5_as_segmentation_object

def convert_sff_to_json(input_file: Path) -> Path:
    '''Converts SFF (hff) to JSON file'''
    json_filepath_str = str((input_file.with_suffix('.json')).resolve())
    segm_obj = open_hdf5_as_segmentation_object(input_file)

    try:
        segm_obj.export(fn=json_filepath_str)
    except AttributeError:
        pass

    return Path(json_filepath_str)

if __name__ == '__main__':
    SFF_PATH = Path("preprocessor/data/raw_input_files/emdb/emd-1832/EMD-1832.hff")
    convert_sff_to_json(SFF_PATH)
