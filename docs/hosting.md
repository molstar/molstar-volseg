# Hosting

This page goes over setting up a local instance of Mol* Volumes and Segmentations server and frontend.

# Obtaining the code & setting up the environment

Clone this GitHub repository: 

```
git clone https://github.com/molstar/molstar-volseg
cd molstar-volseg
```

Create a Conda environment from `environment.yaml` using [Conda](https://conda.io/projects/conda/en/latest/user-guide/install/index.html)

```
conda env create -f environment.yaml
```


or [Mamba](https://mamba.readthedocs.io/en/latest/installation.html)

```
mamba env create -f environment.yaml
```

All subsequent commands need to be run in the created Conda environment after activating it:

```
conda activate cellstar-volume-server
```

# Setting up the database

## Supported formats

- [SFF](https://www.ebi.ac.uk/emdb/documentation#seg_model) (`.hff`) for segmentation data
- CCP4 for volume data (`.map, .mrc, .ccp4 files`)
- Additional formats (`.am, .mod, .seg, .stl`) are supported thought [SFF-TK](https://github.com/emdb-empiar/sfftk) conversion to SFF (`.hff`)

## Adding an entry to the database

The `preprocessor\main.py` script is used for adding entries to the database with the following arguments:

 - `--db_path` - path to folder with database, defaults to `test-data/db`
 - `--single_entry` - path to folder with input files (volume and segmentation)
 - `--entry_id` - entry id (e.g. `emd-1832`) to be used as database folder name for that entry
 - `--source_db` - source database name (e.g. `emdb`) to be used as DB folder name
 - `--source_db_id` - actual source database ID of that entry (will be used to compute metadata)
 - `--source_db_name` - actual source database name (will be used to compute metadata)
 - `--force_volume_dtype` - optional data type of volume data to be used instead of the one used volume file. Not used by default
 - `--quantize_volume_data_dtype_str` - optional data quantization (options are - `u1` or `u2`), less precision, but also requires less storage. Not used by default
 - `--temp_zarr_hierarchy_storage_path` - optional path to directory where temporary files will be stored during the build process. Defaults to `test-data/preprocessor/temp_zarr_hierarchy_storage/${DB_PATH}`


Example:

- Create a folder `inputs/emd-1832`
- Download [MAP](https://ftp.ebi.ac.uk/pub/databases/emdb/structures/EMD-1832/map/emd_1832.map.gz) and extract it to `inputs/emd-1832/emd_1832.map`
- Download [Segmentation](https://www.ebi.ac.uk/em_static/emdb_sff/18/1832/emd_1832.hff.gz) and extract it to `inputs/emd-1832/emd_1832.hff`
- Run

```
python preprocessor\main.py --db_path my_db --single_entry inputs/emd-1832 --entry_id emd-1832 --source_db emdb --source_db_id emd-1832 --source_db_name emdb
```

## Adding segmentation in non-SFF format

There are two options:
- Use application specific segmentation file format directly (we support internal conversion of segmentation data in `.am, .mod, .seg, .stl` formats to SFF via `sfftk` package)
- Use https://sfftk.readthedocs.io/en/latest/converting.html on your own, and then use that SFF (`.hff`) file to add an entry to database as described above

Example:

- Create a folder `inputs/emd-9094`
- Download [`emd_9094.map`](https://ftp.ebi.ac.uk/pub/databases/emdb/structures/EMD-9094/map/emd_9094.map.gz) and extract it to `inputs/emd-9094/emd_9094.map`
- Use [Segger](https://www.cgl.ucsf.edu/chimera/docs/ContributedSoftware/segger/segment.html) to compute a segmentation and store it in `inputs/emd-9094/emd_9094.seg`
- Run

```
python preprocessor\main.py --db_path my_db --single_entry inputs/emd-9094 --entry_id emd-9094 --source_db emdb --source_db_id emd-9094 --source_db_name emdb
```

## Build a Database from a CSV list

From root project directory (`molstar-volseg` by default) run:

```
python preprocessor/src/tools/deploy_db/build.py --csv_with_entry_ids test-data/preprocessor/db_building_parameters_custom_entries.csv
```

This will build db with 11 EMDB entries, and using default values of all other arguments.

Note that building this example may require a lot of RAM.

Supported `build.py` arguments:
 - `--csv_with_entry_ids` - csv file with entry ids and info to preprocess
 - `--raw_input_files_dir` - path to raw input files to preprocess, defaults to `test-data/preprocessor/raw_input_files`
 - `--db_path` - path to db folder, defaults to `test-data/db`
 - `--temp_zarr_hierarchy_storage_path` - path to directory where temporary files will be stored during the build process. Defaults to `test-data/preprocessor/temp_zarr_hierarchy_storage/${DB_PATH}`
	

# Hosting

## Hosting the Mol* Volumes and Segmentations Server

To run the API, specify these environment variables:

- `HOST=0.0.0.0` where to host the server
- `PORT=9000` what port to run the app on
- `DB_PATH=my_db` path to the database folder
- `DEV_MODE=False` if True, runs the server in reload mode

and within the `cellstar-volume-server` conda environment run:

```
cd server
python serve.py
```

Examples:

Linux/Mac:

```
cd server
DEV_MODE=True python serve.py
```

Windows (cmd):

```
cd server
set DEV_MODE=true
python serve.py
```

## Setting up Mol* Viewer

- To view the data, a [Volumes and Segmentations extension](https://github.com/molstar/molstar/tree/master/src/extensions/volumes-and-segmentations) is available as part of the [Mol* Viewer](https://github.com/molstar/molstar). 
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

## Build & Host Script

We use the [build_and_deploy.py](../preprocessor/src/tools/deploy_db/build_and_deploy.py) script to preprocess the database and host the API and Landing Page. Modifying this script might be useful when running the solution on your own data.

To build database, and to run both frontend and api, from `molstar-volseg` directory (default) run:

```
python preprocessor/src/tools/deploy_db/build_and_deploy.py  --csv_with_entry_ids test-data/preprocessor/db_building_parameters_custom_entries.csv	
```

`preprocessor/src/tools/deploy_db/build_and_deploy.py` arguments:

 - `--csv_with_entry_ids` - csv file with entry ids and info to preprocess
 - `--raw_input_files_dir` - path to raw input files to preprocess, defaults to `test-data/preprocessor/raw_input_files`
 - `--db_path` - path to db folder, defaults to `test-data/db`
 - `--temp_zarr_hierarchy_storage_path` - path to directory where temporary files will be stored during the build process. Defaults to `test-data/preprocessor/temp_zarr_hierarchy_storage/${DB_PATH}`
 - `--api_port API_PORT` - api port, defaults to `9000`
 - `--api_hostname` - hostname, defaults to `localhost`
 - `--frontend_port` - frontend port, defaults to `3000`


## Troubleshooting

### `ImportError: libEGL.so.1: cannot open shared object file: No such file or directory)` Error on Debian

- `wget https://ftp.gnu.org/pub/gnu/libiconv/libiconv-1.17.tar.gz`
  - Extract, compile and add path to `LD_LIBRARY_PATH`
- To `/etc/apt/sources.list` add line `deb http://deb.debian.org/debian bullseye main`
- `apt-get update`
- `apt-get install libegl-dev`
