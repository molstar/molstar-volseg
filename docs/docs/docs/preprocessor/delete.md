# delete

Using the `delete` command allows the user to remove an entry from an internal database. While it is possible to achieve the same result by manually deleting an entry folder, using the `delete` command is a more standardized approach that also opens a way for automatization via user-created custom scripts. The command `delete` requires the following arguments:

| Argument | Description |
| -------- | ---------- |
| `--entry_id` (string) | entry ID in internal database, corresponding to the entry folder name (e.g. `emd-1832`)|
| `--source_db` (string) | source database, corresponding to the source database folder name in internal database (e.g. `emdb`)|
| `--db_path` (string) | specifies the path to the internal database |
