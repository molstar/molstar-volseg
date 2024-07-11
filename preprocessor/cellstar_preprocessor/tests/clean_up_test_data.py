

from pathlib import Path

from cellstar_preprocessor.tools.clean_dir.clean_dir import clean_dir


if __name__ == "__main__":
    w = Path('preprocessor/cellstar_preprocessor/tests/test_data/working_folder')
    i = Path('preprocessor/cellstar_preprocessor/tests/test_data/inputs_for_tests')
    clean_dir(w)
    clean_dir(i)