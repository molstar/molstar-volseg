# How to build db (preprocessed zarr structure)
1. Delete all subdirectories from `db\emdb`
2. Place input files in subdirs inside `preprocessor\raw_input_files\emdb`. Each subdir = a signle db entry, name of subdir should correspond to entry name. Inside each subdir there should be `.map` volume file and `.hff` segmentation file for that entry.

*For example:*
`preprocessor\raw_input_files\emdb\emd-1832` is a subdir for `emd-1832` entry (*ideally should be lower case*). It contains `.map` and `.hff` files for that entry. After `main.py` has done its job (see below), it should be converted to `emd-1832` db entry.

3. Make sure there are no directories in ` preprocessor\temp_zarr_hierarchy_storage\` (e.g. temporary files could  be there if previous db build procedure was interrupted or finished unsuccessfully, but they needs to be deleted for building db cleanly from scratch to avoid potential issues)
4. Run `python preprocessor\main.py`
5. Confirm that dict with file pathes printed out by the script is correct
6. Check if there is now some subdir in `db\emdb` (the only one should  be `emd-1832` currently)

