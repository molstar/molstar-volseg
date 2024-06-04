# Usage
## Quick start
To run the Volumes & Segmentations toolkit and produce the static files suitable for visualization at the frontend:

1. Build the internal database by adding desired entries using preprocessor (see [Documentation for preprocess command of Preprocessor](../preprocessor/preprocess.md) and [examples on how to add entries to the internal database](../preprocessor/preprocess#examples-of-using-preprocess-command-in-mode-add.md)) 

2. From repository root (`cellstar-volume-server-v2` by default) run:
```shell
    python --db_path PATH_TO_DB --out OUTPUT_FILE --json-params-path PATH_TO_JSON_WITH_PARAMETERS
```
<!-- TODO: move here text from the paper -->
## Arguments description
| Argument | Description |
| -------- | ----------- |
| `--db_path` | The --db_path argument is mandatory and dictates the path to the internal database constructed using the Preprocessor |
| `--out` | The --out argument is mandatory and specifies the desired name for the output file. This file name must include the mandatory .cvsx extension |
| `--json-params-path` | The --json-params-path argument is obligatory and defines the path to the JSON file containing the user-specified query parameters (see table below) |

### Query parameters
| Parameter         | Description                                                                                                             | Kind      | Type                                        | Default                          |
|-------------------|-------------------------------------------------------------------------------------------------------------------------|-----------|---------------------------------------------|----------------------------------|
| entry_id          | ID of entry in internal database (e.g. emd-1832)                                                                        | mandatory | string                                      | N/A                              |
| source_db         | Source database (e.g. emdb)                                                                                             | mandatory | string                                      | N/A                              |
| segmentation_kind | Kind of segmentation (e.g. lattice)                                                                                     | optional  | 'mesh', 'lattice', 'geometric-segmentation' | all segmentation kinds           |
| time              | Timeframe index                                                                                                         | optional  | integer                                     | all available time frame indices |
| channel_id        | Volume channel ID                                                                                                       | optional  | string                                      | all available channel IDs        |
| segmentation_id   | Segmentation ID                                                                                                         | optional  | string                                      | all available segmentation IDs   |
| max_points        | Maximum number of points for volume and/or lattice segmentation. Used to determine the most suitable downsampling level | optional  | integer                                     | 1000000000000                    |


## Example
This example shows how produce `results.cvsx` CVSX file for `idr-13457537`internal database entry (with the database located in `temp/test_db`) containing the volume data for channel 2 and timeframe index 4, and segmentation data for all available segmentation kinds and timeframe index 4

First create `json_with_query_params.json` file with the following content: 

```json
        "entry_id": "idr-13457537",
        "source_db": "idr",
        "channel_id": "2",
        "time": 4

```

Then use the following command:
    ```
    python vs_toolkit.py --db_path temp/test_db --out results.cvsx composite --json-params-path json_with_query_params.json
    ```
    
This will query data for channel `2` and time frame `4` for volume and data for all available segmentation kinds and time frame `4`, and pack it into `idr-13457537.cvsx` file