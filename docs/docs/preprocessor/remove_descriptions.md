# remove-descriptions
This command allows removing specific description (part of annotations.json specifying biologically relevant information) in `annotations.json` which is a part of internal database entry. Requires the following arguments:

| Argument | Description |
| -------- | ---------- |
| `--entry_id` (string) | entry ID in internal database, corresponding to the entry folder name (e.g. `emd-1832`) |
| `--source_db` (string) | source database, corresponding to the source database folder name in internal database (e.g. `emdb`) |
| `--id` (string) | specifies description UUID (can be obtained from `annotations.json` file)|
|`--db_path` (string) | specifies the path to the internal database |