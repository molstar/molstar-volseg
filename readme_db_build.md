# How to build db (preprocessed zarr structure)
1. Delete all subdirectories from `db\emdb`
2. Make sure there are no directories in ` preprocessor\temp_zarr_hierarchy_storage\` (e.g. temporary files could  be there if previous db build procedure was interrupted or finished unsuccessfully)
3. Run `python preprocessor\main.py`
4. Check if there is now some subdir in `db\emdb` (the only one should  be `emd-1832` currently)

