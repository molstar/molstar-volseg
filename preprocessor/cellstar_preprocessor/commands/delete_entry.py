import typer
from cellstar_db.file_system.db import FileSystemVolumeServerDB


import asyncio
from pathlib import Path

def delete_entry(
    entry_id: str = typer.Option(default=...),
    source_db: str = typer.Option(default=...),
    db_path: str = typer.Option(default=...),
):
    print(f"Deleting db entry: {entry_id} {source_db}")
    new_db_path = Path(db_path)
    if new_db_path.is_dir() == False:
        new_db_path.mkdir()

    db = FileSystemVolumeServerDB(new_db_path, store_type="zip")
    asyncio.run(db.delete(namespace=source_db, key=entry_id))