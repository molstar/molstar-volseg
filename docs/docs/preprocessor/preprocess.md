# preprocess

The `preprocess` command of `preprocessor/cellstar_preprocessor/preprocess.py` script is used for adding entries to the database. It requires the following arguments:

  | Argument | Description |
  | -------- | ---------- |
  |`--mode` | Either `add` (adding entry to the database) or `extend` (extend data of existing entry) |
  |`--quantize-dtype-str` | Optional data quantization (options are - `u1` or `u2`), less precision, but also requires less storage. Not used by default |
  |`--quantize-downsampling-levels` | Specify which downsampling level should be quantized as a sequence of numbers, e.g. `1 2`. Not used by default |
  |`--force-volume-dtype` | optional data type of volume data to be used instead of the one used volume file. Not used by default |
  |`--max-size-per-downsampling-lvl-mb` | Maximum size of data per downsampling level in MB. Used to deterimine the number of downsampling steps data from which will be stored |
  |`--min-size-per-downsampling-lvl-mb` | Minimum size of data per downsampling level in MB. Used to deterimine the number of downsampling steps data from which will be stored. Default is `5` |
  |`--min-downsampling-level` | Minimum downsampling level |
  |`--max-downsampling-level` | Maximum downsampling level |
  |`--remove-original-resolution` | Optional flag for removing original resolution data |
  |`--entry-id` | entry id (e.g. `emd-1832`) to be used as database folder name for that entry |
  |`--source-db` | source database name (e.g. `emdb`) to be used as DB folder name |
  |`--source-db-id` | actual source database ID of that entry (will be used to compute metadata) |
  |`--source-db-name` | actual source database name (will be used to compute metadata) |
  |`--working-folder` | path to directory where temporary files will be stored during the build process |
  |`--db-path` | path to folder with database |
  |`--input-path` | Path to input file. Should be provided for each input file separately (see examples) |
  |`--input-kind` | Kind of input file. One of the following: <code>[map\|sff\|omezarr\|mask\|application_specific_segmentation\|custom_annotations\|nii_volume\|nii_segmentation\|geometric_segmentation\|star_file_geometric_segmentation\|ometiff_image\|ometiff_segmentation\|extra_data]</code>. See examples for more details. |


As one can see, `preprocess` command has two possible modes for the `preprocess`: `add` and `extend`.

## preprocess --mode add
In case of `add` mode, an entry will be created based on the input files and parameters provided.


Example of usage of mode `add`:

```shell
python preprocessor/cellstar_preprocessor/preprocess.py preprocess --mode add --input-path test-data/preprocessor/sample_volumes/emdb/EMD-1832.map --input-kind map --entry-id emd-1832 --source-db emdb --source-db-id emd-1832 --source-db-name emdb --working-folder temp_working_folder --db-path preprocessor/temp/test_db
```

This command will add an `emd-1832` entry to the internal database, throwing an exception if this entry already exists.


## prepocess --mode extend

Another option is mode `extend` which will extend the entry data with e.g. additional segmentation. For example, initially an `emd-1832` entry may be added to the database using mode `add` (see code listing above). Note that at this point it contains only the volume data as we provided only the electron density map as input.

Then the user may decide to add segmentation data to it. This can be achieved using mode `extend` of `preprocess` command:

```shell
python preprocessor/cellstar_preprocessor/preprocess.py preprocess --mode extend --input-path test-data/preprocessor/sample_segmentations/emdb_sff/emd_1832.hff --input-kind sff --entry-id emd-1832 --source-db emdb --source-db-id emd-1832 --source-db-name emdb --working-folder temp_working_folder --db-path preprocessor/temp/test_db
```

Note that the values of arguments `--entry-id`, `--source-db`, `--source-db-id`, `--source-db-name`, and `--db-path` should be exactly the same as the ones used when the entry was initially created using mode `add`. After using this command, the `emd-1832` entry will have not only volume data, but also lattice segmentation data based on the provided EMDB SFF file.


## Examples of using preprocess command in mode add

### EMD-1832
<!-- - Create a folder `inputs/emd-1832`
- Download [MAP](https://ftp.ebi.ac.uk/pub/databases/emdb/structures/EMD-1832/map/emd_1832.map.gz) and extract it to `inputs/emd-1832/emd_1832.map`
- Download [Segmentation](https://www.ebi.ac.uk/em_static/emdb_sff/18/1832/emd_1832.hff.gz) and extract it to `inputs/emd-1832/emd_1832.hff` -->

- To add an emd-1832 entry to the internal database, from root directory (`molstar-volseg` by default) run:

```
python preprocessor/cellstar_preprocessor/preprocess.py preprocess --mode add --input-path test-data/preprocessor/sample_volumes/emdb/EMD-1832.map --input-kind map --input-path test-data/preprocessor/sample_segmentations/emdb_sff/emd_1832.hff --input-kind sff --entry-id emd-1832 --source-db emdb --source-db-id emd-1832 --source-db-name emdb --working-folder temp_working_folder --db-path preprocessor/temp/test_db --quantize-dtype-str u1
```

It will add entry `emd-1832` to the database and during preprocessing volume data will be quantized with `u1` option

### IDR-13457537
- First unzip `test-data/preprocessor/sample_segmentations/idr/13457537.zarr.zip` file. E.g. from the root repository directory (`molstar-volseg` by default) run:
```
cd test-data/preprocessor/sample_segmentations/idr/idr-13457537
unzip 13457537.zarr.zip
```

To add entry to the database, from the root repository directory (`molstar-volseg` by default) run e.g.:
```
python preprocessor/cellstar_preprocessor/preprocess.py preprocess --mode add --input-path test-data/preprocessor/sample_segmentations/idr/idr-13457537/13457537.zarr --input-kind omezarr --entry-id idr-13457537 --source-db idr --source-db-id idr-13457537 --source-db-name idr --working-folder temp_working_folder --db-path preprocessor/temp/test_db
```

It will add entry `idr-13457537` to the database.

### EMD-1832-geometric-segmentation

- To add an emd-1832 entry with artificially created geometric segmentation to the internal database, from root directory (`molstar-volseg` by default) run e.g.:

```
python preprocessor/cellstar_preprocessor/preprocess.py preprocess --mode add --input-path test-data/preprocessor/sample_volumes/emdb/EMD-1832.map --input-kind map --input-path test-data/preprocessor/sample_segmentations/geometric_segmentations/geometric_segmentation_1.json --input-kind geometric_segmentation --input-path test-data/preprocessor/sample_segmentations/geometric_segmentations/geometric_segmentation_2.json --input-kind geometric_segmentation  --entry-id emd-1832-geometric-segmentation --source-db emdb --source-db-id emd-1832-geometric-segmentation --source-db-name emdb --working-folder temp_working_folder --db-path preprocessor/temp/test_db
```

It will add entry `emd-1832-geometric-segmentation` to the database

### EMD-1273 with segmentations based on masks
<!-- - Create a folder `inputs/emd-1832` -->
1. Download [MAP](https://ftp.ebi.ac.uk/pub/databases/emdb/structures/EMD-1273/map/emd_1273.map.gz) and extract it to `test-data/preprocessor/sample_volumes/emdb/`
2. Create folder `test-data/preprocessor/sample_segmentations/emdb_masks/` if not exists
3. Download masks to `test-data/preprocessor/sample_segmentations/emdb_masks/`:
    - [Mask 1](https://ftp.ebi.ac.uk/pub/databases/emdb/structures/EMD-1273/masks/emd_1273_msk_1.map)
    - [Mask 2](https://ftp.ebi.ac.uk/pub/databases/emdb/structures/EMD-1273/masks/emd_1273_msk_2.map)
    - [Mask 3](https://ftp.ebi.ac.uk/pub/databases/emdb/structures/EMD-1273/masks/emd_1273_msk_3.map)
    - [Mask 4](https://ftp.ebi.ac.uk/pub/databases/emdb/structures/EMD-1273/masks/emd_1273_msk_4.map)
    - [Mask 5](https://ftp.ebi.ac.uk/pub/databases/emdb/structures/EMD-1273/masks/emd_1273_msk_5.map)

4. To add an `emd-1273` entry with segmentations based on masks to the internal database, from root directory (`molstar-volseg` by default) run:

```
python preprocessor/cellstar_preprocessor/preprocess.py preprocess --mode add --input-path test-data/preprocessor/sample_volumes/emdb/emd_1273.map --input-kind map --input-path test-data/preprocessor/sample_segmentations/emdb_masks/emd_1273_msk_1.map --input-kind mask --input-path test-data/preprocessor/sample_segmentations/emdb_masks/emd_1273_msk_2.map --input-kind mask --input-path test-data/preprocessor/sample_segmentations/emdb_masks/emd_1273_msk_3.map --input-kind mask --input-path test-data/preprocessor/sample_segmentations/emdb_masks/emd_1273_msk_4.map --input-kind mask --input-path test-data/preprocessor/sample_segmentations/emdb_masks/emd_1273_msk_5.map --input-kind mask --entry-id emd-1273 --source-db emdb --source-db-id emd-1273 --source-db-name emdb --working-folder temp_working_folder --db-path preprocessor/temp/test_db
```

### EMPIAR-10988


In order to add an `empiar-10988` entry with lattice segmentations based on masks to the internal database, follow the steps below:

1. Obtain the raw input files:

	Create `test-data/preprocessor/sample_volumes/empiar/empiar-10988` folder, change current directory to it, and download electron density map file. E.g. from the root repository directory (`molstar-volseg` by default) run:

    ```shell
    mkdir -p test-data/preprocessor/sample_volumes/empiar/empiar-10988
    cd test-data/preprocessor/sample_volumes/empiar/empiar-10988
    wget https://ftp.ebi.ac.uk/empiar/world_availability/10988/data/DEF/tomograms/TS_026.rec
	```

	Next, create `test-data/preprocessor/sample_segmentations/empiar/empiar-10988` directory, change current directory to it, and download electron density mask files. E.g. from the root repository directory (`molstar-volseg` by default) run:

    
    ```shell
    mkdir -p test-data/preprocessor/sample_segmentations/empiar/empiar-10988
    cd test-data/preprocessor/sample_segmentations/empiar/empiar-10988
    wget https://ftp.ebi.ac.uk/empiar/world_availability/10988/data/DEF/labels/TS_026.labels.mrc
    wget https://ftp.ebi.ac.uk/empiar/world_availability/10988/data/DEF/labels/TS_026_cyto_ribosomes.mrc
    wget https://ftp.ebi.ac.uk/empiar/world_availability/10988/data/DEF/labels/TS_026_cytosol.mrc
    wget https://ftp.ebi.ac.uk/empiar/world_availability/10988/data/DEF/labels/TS_026_fas.mrc
    wget https://ftp.ebi.ac.uk/empiar/world_availability/10988/data/DEF/labels/TS_026_membranes.mrc
    ```

2. Prepare extra data

    By default, Preprocessor will use segment IDs based on grid values in mask file. It is possible to overwrite them using additional input file with extra data, mapping segment IDs used by default (e.g. "1", "2" etc.) to biologically meaningful segment IDs (e.g., "cytoplasm", "mitochondria" etc.).
    Create `extra_data_empiar_10988.json` file in root repository directory with the following content:
    ```json
    {
        "segmentation": {
            "segment_ids_to_segment_names_mapping": {
                "TS_026.labels": {
                    "1": "cytoplasm",
                    "2": "mitochondria",
                    "3": "vesicle",
                    "4": "tube",
                    "5": "ER",
                    "6": "nuclear envelope",
                    "7": "nucleus",
                    "8": "vacuole",
                    "9": "lipid droplet",
                    "10": "golgi",
                    "11": "vesicular body",
                    "13": "not identified compartment"
                }
            }
        }
    }
    ```

  The content of the file is based on the content of `10988/data/DEF/labels/organelle_labels.txt` from [EMPIAR-10988 webpage](https://www.ebi.ac.uk/empiar/EMPIAR-10988/). It maps the segment IDs for segmentation from `TS_026.labels.mrc` file to biologically relevant segment names.

3. Add `empiar-10988` entry to the internal database

    In order to add an `empiar-10988` entry with segmentations based on masks to the internal database, from root directory (`molstar-volseg` by default) run:
    
```shell
    python preprocessor/cellstar_preprocessor/preprocess.py preprocess --mode add --input-path extra_data_empiar_10988.json --input-kind extra_data --input-path test-data/preprocessor/sample_volumes/empiar/empiar-10988/TS_026.rec --input-kind map --input-path test-data/preprocessor/sample_segmentations/empiar/empiar-10988/TS_026.labels.mrc --input-kind mask --input-path test-data/preprocessor/sample_segmentations/empiar/empiar-10988/TS_026_membranes.mrc --input-kind mask --input-path test-data/preprocessor/sample_segmentations/empiar/empiar-10988/TS_026_fas.mrc --input-kind mask --input-path test-data/preprocessor/sample_segmentations/empiar/empiar-10988/TS_026_cytosol.mrc --input-kind mask --input-path test-data/preprocessor/sample_segmentations/empiar/empiar-10988/TS_026_cyto_ribosomes.mrc --input-kind mask --min-downsampling-level 4 --remove-original-resolution --entry-id empiar-10988 --source-db empiar --source-db-id empiar-10988 --source-db-name empiar --working-folder temp_working_folder --db-path preprocessor/temp/test_db
```

Note that we are setting minimum downsampling level to `4` by using `--min-downsampling-level` argument and removing original resolution via `--remove-original-resolution` argument. The reason for this is that rendering of the original resolution data, and even the 2nd downsampling is computationally demanding. It is not related to the application itself, but rather to the size and complexity of the dataset.   

### EMPIAR-11756
In order to add an empiar-11756 entry with geometric segmentation to the internal database, follow the steps below:

1. Obtain the raw input files

	Create `test-data/preprocessor/sample_volumes/empiar/empiar-11756` folder, change current directory to it, and download electron density map file. E.g. from the root repository directory (`molstar-volseg` by default) run:

    ```shell
    mkdir -p test-data/preprocessor/sample_volumes/empiar/empiar-11756
    cd test-data/preprocessor/sample_volumes/empiar/empiar-11756
    wget https://ftp.ebi.ac.uk/empiar/world_availability/11756/data/tomoman_minimal_project/cryocare_bin4_tomoname/17072022_BrnoKrios_Arctis_p3ar_grid_Position_35.mrc
	```

	Next, create `test-data/preprocessor/sample_segmentations/empiar/empiar-11756` directory, change current directory to it, and download two `.star` files. E.g. from the root repository directory (`molstar-volseg` by default) run:

    
    ```shell
    mkdir -p test-data/preprocessor/sample_segmentations/empiar/empiar-11756
    cd test-data/preprocessor/sample_segmentations/empiar/empiar-11756
    wget https://ftp.ebi.ac.uk/empiar/world_availability/11756/data/tomoman_minimal_project/17072022_BrnoKrios_Arctis_p3ar_grid_Position_35/metadata/particles/rln_nucleosome_bin1_tomo_649.star
    wget https://ftp.ebi.ac.uk/empiar/world_availability/11756/data/tomoman_minimal_project/17072022_BrnoKrios_Arctis_p3ar_grid_Position_35/metadata/particles/rln_ribosome_bin1_tomo_649.star
    ```

2. Prepare input files.

	This EMPIAR entry contains relevant data that can be used to render geometric segmentation in `.star` format. To be able to use this data, .star files need to be parsed into the standard Mol\* VS 2.0 format for geometric segmentations. This can be achieved by using custom script `preprocessor/cellstar_preprocessor/tools/parse_star_file/parse_single_star_file.py` that is part of our solution. In parallel, this script allows to set the biologically meaningful segmentation IDs for both geometric segmentations based on the data from EMPIAR entry webpage (i.e. `ribosomes` and `nucleosomes`). In order to parse both `.star` files, from the root repository directory (`molstar-volseg` by default) run:

    ```shell
    python preprocessor/cellstar_preprocessor/tools/parse_star_file/parse_single_star_file.py --star_file_path test-data/preprocessor/sample_segmentations/empiar/empiar-11756/rln_ribosome_bin1_tomo_649.star --geometric_segmentation_input_file_path test-data/preprocessor/sample_segmentations/empiar/empiar-11756/geometric_segmentation_input_1.json --sphere_radius 100 --segmentation_id ribosomes  --sphere_color_hex FFFF00 --pixel_size 7.84 --star_file_coordinate_divisor 4
    ```

    ```shell
    python preprocessor/cellstar_preprocessor/tools/parse_star_file/parse_single_star_file.py --star_file_path test-data/preprocessor/sample_segmentations/empiar/empiar-11756/rln_nucleosome_bin1_tomo_649.star --geometric_segmentation_input_file_path test-data/preprocessor/sample_segmentations/empiar/empiar-11756/geometric_segmentation_input_2.json --sphere_radius 100  --segmentation_id nucleosomes --sphere_color_hex FF0000 --pixel_size 7.84 --star_file_coordinate_divisor 4
    ```

    Besides the volume map file from EMPIAR entry webpage has wrong header parameters (voxel size is 0 for all 3 spatial dimensions). To alleviate this, one can use functionality of Preprocessor that allows to overwrite database entry parameters during preprocessing. Based on the data from EMPIAR entry webpage, voxel size should be `1.96` Angstrom for all 3 dimensions. Since we use volume map file from cryocare_bin4_tomoname folder, this value needs to be multiplied by 4, which gives us `7.84` Angstrom. According to this, create `test-data/preprocessor/sample_volumes/empiar/empiar-11756/empiar-11756-extra-data.json` file with the following content:

    ```json
    {
        "volume": {
            "voxel_size": [
                7.84,
                7.84,
                7.84
            ]
        }   
    }
    ```


3. Add empiar-11756 entry to the internal database

    To add an empiar-11756 entry with segmentations based on masks to the internal database, from root directory (`molstar-volseg` by default) run:


    ```shell
    python preprocessor/cellstar_preprocessor/preprocess.py preprocess --mode add --input-path test-data/preprocessor/sample_volumes/empiar/empiar-11756/empiar-11756-extra-data.json --input-kind extra_data --input-path test-data/preprocessor/sample_volumes/empiar/empiar-11756/17072022_BrnoKrios_Arctis_p3ar_grid_Position_35.mrc --input-kind map --input-path test-data/preprocessor/sample_segmentations/empiar/empiar-11756/geometric_segmentation_input_1.json --input-kind geometric_segmentation --input-path test-data/preprocessor/sample_segmentations/empiar/empiar-11756/geometric_segmentation_input_2.json --input-kind geometric_segmentation --entry-id empiar-11756 --source-db empiar --source-db-id empiar-11756 --source-db-name empiar --working-folder temp_working_folder --db-path preprocessor/temp/test_db
    ```

    It will create a database entry with two geometric segmentations (segmentation IDs `ribosomes` and `nucleosomes`).


### CUSTOM-hipsc_230741
<!-- TODO: change -->
<!-- TODO: structure of the dataset -->
#### Introduction to hipsc_single_cell_image_dataset structure
Structure of the hipsc_single_cell_image_dataset is explained in [readme](https://open.quiltdata.com/b/allencell/tree/aics/hipsc_single_cell_image_dataset/README.md). In this example we will use imaging data and metadata for cell with CellID 230,741 (the first row in [metadata.csv](https://open.quiltdata.com/b/allencell/tree/aics/hipsc_single_cell_image_dataset/metadata.csv)).

#### Adding entry to the internal database
In order to add an custom-hipsc_230741 entry to the internal database, follow the steps below:

1. Obtain the raw input files

	Create `test-data/preprocessor/sample_volumes/custom/custom-hipsc_230741` folder, change current directory to it, and download OME-TIFF file with volume data. E.g. from the root repository directory (`molstar-volseg` by default) run:

    ```shell
    mkdir -p test-data/preprocessor/sample_volumes/custom/custom-hipsc_230741
    cd test-data/preprocessor/sample_volumes/custom/custom-hipsc_230741
    wget -O hipsc_230741_volume.ome.tif https://allencell.s3.amazonaws.com/aics/hipsc_single_cell_image_dataset/crop_raw/7922e74b69b77d6b51ea5f1627418397ab6007105a780913663ce1344905db5c_raw.ome.tif?versionId=yQ6YaOj1YgDNgS4DpsnmrNAkOQ.4pgS6
	```

	Next, create `test-data/preprocessor/sample_segmentations/custom/custom-hipsc_230741` directory, change current directory to it, and download OME-TIFF file with segmentation data. E.g. from the root repository directory (`molstar-volseg` by default) run: 

    
    ```shell
    mkdir -p test-data/preprocessor/sample_segmentations/custom/custom-hipsc_230741
    cd test-data/preprocessor/sample_segmentations/custom/custom-hipsc_230741
    wget -O hipsc_230741_segmentation.ome.tif https://allencell.s3.amazonaws.com/aics/hipsc_single_cell_image_dataset/crop_seg/a9a2aa179450b1819f0dfc4d22411e6226f22e3c88f7a6c3f593d0c2599c2529_segmentation.ome.tif?versionId=hf7gc1GKeDjgVYeNBEdmvV0w2NUJS38_
    ```

2. Prepare addtional input files.
    
    OMETIFF input files with volume and segmentation data contains incomplete information for preprocessing and subsequent rendering. To alleviate this, one can create JSON file with extra data, based on the content of [metadata.csv](https://open.quiltdata.com/b/allencell/tree/aics/hipsc_single_cell_image_dataset/metadata.csv).
    Namely, we need to set voxel size, biologically meaningfull channel IDs for volume data and segmentation IDs for segmentation data, and specify missing OME-TIFF dimenstions. Besides, we can add biologically relavant annotation information (cell stage) that will be rendered in the Mol\* VS 2.0 user interface. 

    We can extract the necessary information from [metadata.csv](https://open.quiltdata.com/b/allencell/tree/aics/hipsc_single_cell_image_dataset/metadata.csv) using the following approach:

     - **Voxel size**: value of `scale_micron` field (`[0.108333, 0.108333, 0.108333]`) converted to Angstroms (`[1083.33, 1083.33, 1083.33]`)
     - **Biologically meaningful channel IDs**: can be obtained from content of `name_dict` field, which corresponds to Python dictionary. We need the value of `crop_raw` key (`['dna', 'membrane', 'structure']`)
     - **Biologically meaningful segmentation IDs**: can be obtained from content of `name_dict` field as well. We need the value of `crop_seg` key (` ['dna_segmentation', 'membrane_segmentation', 'membrane_segmentation_roof', 'struct_segmentation', 'struct_segmentation_roof']`)
     - **Missing OME-TIFF dimensions**: is not specified anywhere. To obtain this, we will need to open OME-TIFF file using `pyometiff` library that should be installed by default while creating the environment for Mol\* VS 2.0. 
     
        You can run `python preprocessor/cellstar_preprocessor/tools/check_ometiff_dimensions/check_ometiff_dimensions.py` script to check the dimensions of OME-TIFF file:

        ```shell
        python preprocessor/cellstar_preprocessor/tools/check_ometiff_dimensions/check_ometiff_dimensions.py
        ```

        The output of this script should look like this:
        ```
            Opening hipsc_230741_volume.ome.tif
            Key not found: list index out of range
            Key not found: list index out of range
            key not found list index out of range
            Key not found: list index out of range
            hipsc_230741_volume.ome.tif
            Dimension order:  TZCYX
            Data array shape (119, 3, 281, 268)
            Opening hipsc_230741_segmentation.ome.tif
            Key not found: list index out of range
            Key not found: list index out of range
            key not found list index out of range
            Key not found: list index out of range
            hipsc_230741_segmentation.ome.tif
            Dimension order:  TZCYX
            Data array shape (119, 5, 281, 268)
        ```

        As you can see, the output for both volume and segmentation file is the same:
        ```
            Dimension order:  TZCYX
            Data array shape (119, 3, 281, 268)
        ```
        It is obvious that the number of dimensions (5) does not correspond to array shape. In that case, most likely time dimension (`T`) is missing from the data array.
    
     - **Biologically relevant annotations**: We can add biologically relevant annotation data available in [metadata.csv](https://open.quiltdata.com/b/allencell/tree/aics/hipsc_single_cell_image_dataset/metadata.csv). Namely, the content of `cell_stage` field, which, for that cell ID is `M4M5`. 

    Now, when we have obtained all the missing information, create `test-data/preprocessor/sample_segmentations/custom/custom-hipsc_230741/extra_data.json` JSON file with the following content:
    ```json
    {
        "volume": {
            "voxel_size": [
                0.108333,
                0.108333,
                0.108333
            ],
            "channel_ids_mapping": {
                "0": "dna",
                "1": "membrane",
                "2": "structure"
            },
            "dataset_specific_data": {
                "ometiff": {
                    "cell_stage": "M4M5",
                    "missing_dimensions": ["T"]
                }
            }
        },
        "segmentation": {
            "voxel_size": [
                0.108333,
                0.108333,
                0.108333
            ],
            "segmentation_ids_mapping": {
                "0": "dna_segmentation",
                "1": "membrane_segmentation",
                "2": "membrane_segmentation_roof",
                "3": "struct_segmentation",
                "4": "struct_segmentation_roof"
            },
            "dataset_specific_data": {
                "ometiff": {
                    "cell_stage": "M4M5",
                    "missing_dimensions": ["T"]
                }
            }
        }
    }
    ``` 

3. Add custom-hipsc_230741 entry to the internal database

    To add a custom-hipsc_230741 entry to the internal database, from root directory (`molstar-volseg`) run:

    ```shell
    python preprocessor/cellstar_preprocessor/preprocess.py preprocess --mode add --input-path test-data/preprocessor/sample_segmentations/custom/custom-hipsc_230741/extra_data.json --input-kind extra_data --input-path test-data/preprocessor/sample_volumes/custom/custom-hipsc_230741/hipsc_230741_volume.ome.tif --input-kind ometiff_image --input-path test-data/preprocessor/sample_segmentations/custom/custom-hipsc_230741/hipsc_230741_segmentation.ome.tif --input-kind ometiff_segmentation --entry-id custom-hipsc_230741 --source-db custom --source-db-id custom-hipsc_230741 --source-db-name custom --working-folder temp_working_folder --db-path preprocessor/temp/test_db
    ```
