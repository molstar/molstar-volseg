import typer
from cellstar_db.file_system.annotations_context import AnnnotationsEditContext
from cellstar_db.file_system.db import FileSystemVolumeServerDB
from cellstar_db.models import DescriptionData
from cellstar_preprocessor.flows.common import read_json


import asyncio
from pathlib import Path

def edit_descriptions(
    entry_id: str = typer.Option(default=...),
    source_db: str = typer.Option(default=...),
    # id: list[str] = typer.Option(default=...),
    data_json_path: str = typer.Option(default=...),
    db_path: str = typer.Option(default=...),
):
    # print(f"Deleting descriptions for entry: {entry_id} {source_db}")
    new_db_path = Path(db_path)
    if new_db_path.is_dir() == False:
        new_db_path.mkdir()

    db = FileSystemVolumeServerDB(new_db_path, store_type="zip")

    parsedDescriptionData: list[DescriptionData] = read_json(Path(data_json_path))

    with db.edit_annotations(
        namespace=source_db, key=entry_id
    ) as db_edit_annotations_context:
        db_edit_annotations_context: AnnnotationsEditContext
        asyncio.run(
            db_edit_annotations_context.add_or_modify_descriptions(
                parsedDescriptionData
            )
        )