# How to create fake db entries from the real volume files
1. Remove all previously existing files and dirs from `preprocessor/fake_raw_input_files` (segmentation files used to create db entries will be created there, and volumes will be copied there by the script) and `db/emdb` (if it exists, actual db entries will be created there by the script)
2. Place input volume `.map` or `.ccp4` files in `preprocessor/real_volumes_for_converstion_to_fake_sff`
3. Run `preprocessor/create_fake_db_entries_from_input_volumes.py`
4. Created entries will be inside `db/emdb`