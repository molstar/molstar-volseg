from cellstar_db.models import StoreType
import typer
from cellstar_db.file_system.db import FileSystemVolumeServerDB
from cellstar_db.file_system.volume_and_segmentation_context import VolumeAndSegmentationContext


from pathlib import Path


def remove_segmentation(
    entry_id: str = typer.Option(default=...),
    source_db: str = typer.Option(default=...),
    id: str = typer.Option(default=...),
    kind: str = typer.Option(default=...),
    db_path: str = typer.Option(default=...),
    working_folder: str = typer.Option(default=...),
):
    print(f"Deleting segmentation for entry: {entry_id} {source_db}")
    new_db_path = Path(db_path)
    if new_db_path.is_dir() == False:
        new_db_path.mkdir()

    db = FileSystemVolumeServerDB(new_db_path, store_type=StoreType.zip)

    with db.edit_data(
        namespace=source_db, key=entry_id, working_folder=Path(working_folder)
    ) as db_edit_context:
        db_edit_context: VolumeAndSegmentationContext
        db_edit_context.remove_segmentation(id=id, kind=kind)