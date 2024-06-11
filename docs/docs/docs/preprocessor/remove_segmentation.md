# remove-segmentation

This command allows removing specific segmentation data from an internal database entry. Requires the following arguments:

| Argument | Description |
| -------- | ---------- |
| `--entry_id` (string) | entry ID in internal database, corresponding to the entry folder name (e.g. `emd-1832`)
source_db (string) - source database, corresponding to the source database folder name in internal database (e.g. `emdb`)|
| `--id` (string) | specifies segmentation ID (e.g. `0`, `ribosomes`) |
| `--kind` (string) | specifies the segmentation kind (one of the following: `lattice`, `mesh`, `geometric_segmentation`)
| `--db_path` (string) | specifies the path to the internal database |
| `--working_folder` (string) | specifies the path to folder used by Preprocessor for temporary files and data manipulation |
