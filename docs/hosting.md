# Introduction
This tutorial will help you to set up your local copy of Cellstar server and explain how to use it (add entries, host server and frontend etc.)

# Getting local copy of Cellstar server
Clone github repository: https://github.com/molstar/cellstar-volume-server

# Setting up the environment
Create conda environment from environment.yaml, e.g.:
conda env create -f environment.yaml

You can use conda: https://conda.io/projects/conda/en/latest/user-guide/install/index.html

Or mamba: 
https://mamba.readthedocs.io/en/latest/installation.html
mamba env create -f environment.yaml

# Setting up the database
## Supported formats
SFF (.hff) for segmentation data, CCP4 for volume data(.map, .mrc, .ccp4 files). Additionally, as an experimental feature, we support also segmentation data in .am, .mod, .seg, .stl formats through conversion to SFF (.hff).

## Adding an entry to the database
To add entry to the database from root project directory (cellstar-volume-server by default) run preprocessor\main.py with the following arguments:

 - `--db_path` - path to folder with database, default -  - test-data/db
 - `--single_entry` - path to folder with input files (volume and segmentation)
 - `--entry_id` - entry id (e.g. emd-1832) to be used as database folder name for that entry
 - `--source_db` - source database name (e.g. emdb) to be used as DB folder name
 - `--source_db_id` - actual source database ID of that entry (will be used to compute metadata). 
 - `--source_db_name` - actual source database name (will be used to compute metadata)

Optionally, specify also:
 - `--force_volume_dtype` - data type of volume data to be used instead of the one used volume file. Not used by default
 - `--quantize_volume_data_dtype_str` - quantize data (options are - u1 or u2), less precision, but also requires less storage. Not used by default
 - `--temp_zarr_hierarchy_storage_path` - path to directory where temporary files will be stored during the build process. Default - test-data/preprocessor/temp_zarr_hierarchy_storage/YOUR_DB_PATH

## Preprocessing and adding custom segmentations

There are two options - either use application specific segmentation file format directly (we support internal conversion of segmentation data in .am, .mod, .seg, .stl formats to SFF via sfftk package), or use https://sfftk.readthedocs.io/en/latest/converting.html on your own, and then use that SFF (.hff file) to add an entry to database as described in “Adding an entry to the database” section.

We describe the first option here. For example, you have Segger segmentation (emd_9094.seg) for emd-9094 and corresponding volume map (emd_9094.map). Then follow all the steps described in “Adding an entry to the database”, but instead of .hff file, place your emd_9094.seg file into the folder specified as --single_entry argument. During the build process, .hff file will appear in that folder, and will be used to add entry to the database.
Note that if you won’t delete application specific segmentation file from that folder, and run adding entry to the database again, it will convert it again to SFF (.hff) and replace previously converted SFF.

## Build database script
Activate created conda environment, e.g.
```
conda activate cellstar-volume-server
```
From root project directory (cellstar-volume-server by default) run:
```
python preprocessor/src/tools/deploy_db/build.py  --csv_with_entry_ids test-data/preprocessor/db_building_parameters_custom_entries.csv
```

This will build db with 11 EMDB entries, and using default values of all other arguments.
Arguments description:
 - `--csv_with_entry_ids` - csv file with entry ids and info for preprocessor, default - test-data\preprocessor\db_building_parameters_all_entries.csv (not recommended to use default for users, as it requires static files to be hosted at specific location, use --csv_with_entry_ids test-data/preprocessor/db_building_parameters_custom_entries.csv instead)
 - `--raw_input_files_dir` dir with raw input files for preprocessor, default - test-data/preprocessor//raw_input_files
 - `--db_path` - path to db folder, default - test-data/db
 - `--temp_zarr_hierarchy_storage_path` - path to directory where temporary files will be stored during the build process. Default - test-data/preprocessor/temp_zarr_hierarchy_storage/YOUR_DB_PATH

	

# Hosting
## Hosting the Mol* VolumeServer
To run the API, from .\server subdirectory, run `python serve.py`. Script uses the following environment variables (with defaults):
- `HOST=0.0.0.0` where to host the server
- `PORT=9000` what port to run the app on
- `DB_PATH=test-data/db` path to the database folder
- `DEV_MODE=False` if True, runs the server in reload mode

Examples:

Linux/Mac

```
cd server
DEV_MODE=True python serve.py
```

Windows

```
cd server
set DEV_MODE=True && python serve.py
```

## Viewer

- To view the data, a Volumes and Segmentations extension is available as part of the [main Mol* Viewer](https://github.com/molstar/molstar). 
- Please refer to [Mol* Docs](https://molstar.org/docs/) for installing the plugin.
- You can provide the URL to your server instance as `volumesAndSegmentationsDefaultServer` option when creating the [Viewer instance](https://molstar.org/docs/plugin/#viewer-wrapper), e.g.
```ts
molstar.Viewer.create('app', {
    // other options
    volumesAndSegmentationsDefaultServer: 'https://my.org/volumes-and-segmentations/v2'
}).then(viewer => { 
    // ...
})
```

# All-in-one solution
How to build database and run both API and frontend 
To build database, and to run both frontend and api, from cellstar-volume-server directory (default) run:
```
python preprocessor/src/tools/deploy_db/build_and_deploy.py  --csv_with_entry_ids test-data/preprocessor/db_building_parameters_custom_entries.csv	
```

This will build db with 11 EMDB entries, and using default values of all other arguments, and run both API and frontend.

Optionally, add arguments:
 - `--csv_with_entry_ids` - csv file with entry ids and info for preprocessor, default - test-data\preprocessor\db_building_parameters_all_entries.csv (not recommended to use default for users, as it requires static files to be hosted at specific location, use --csv_with_entry_ids test-data/preprocessor/db_building_parameters_custom_entries.csv instead)
 - `--raw_input_files_dir` - dir with raw input files for preprocessor, default - test-data/preprocessor//raw_input_files
 - `--db_path` - path to db folder, default - test-data/db
 - `--temp_zarr_hierarchy_storage_path` - path to directory where temporary files will be stored during the build process. Default - test-data/preprocessor/temp_zarr_hierarchy_storage/YOUR_DB_PATH
 - `--api_port API_PORT` - default api port - 9000
 - `--api_hostname` - default host - '0.0.0.0', localhost
 - `--frontend_port`  - default frontend port - 3000



CSV example of required format:

# TODO