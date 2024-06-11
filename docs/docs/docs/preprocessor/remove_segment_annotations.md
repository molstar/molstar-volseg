# remove-segment-annotations

This command allows removing specific segment annotations from an internal database entry. Requires the following arguments:

| Argument | Description |
| -------- | ---------- |
| `--entry_id` (string) | entry ID in internal database, corresponding to the entry folder name (e.g. `emd-1832`) |
| `--source_db` (string) | source database, corresponding to the source database folder name in internal database (e.g. `emdb`) |
| `--id` (string) | specifies segment annotation UUID (can be obtained from annotations.json file) |
| `--db_path` (string) | specifies the path to the internal database |