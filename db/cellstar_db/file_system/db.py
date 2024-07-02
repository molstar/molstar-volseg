import json
import os
import shutil
from argparse import ArgumentError
from pathlib import Path

import zarr
from cellstar_db.file_system.annotations_context import AnnnotationsEditContext
from cellstar_db.file_system.constants import (
    ANNOTATION_METADATA_FILENAME,
    DB_NAMESPACES,
    GEOMETRIC_SEGMENTATION_FILENAME,
    GRID_METADATA_FILENAME,
    VOLUME_DATA_GROUPNAME,
    ZIP_STORE_DATA_ZIP_NAME,
)
from cellstar_db.file_system.models import FileSystemVolumeMedatada
from cellstar_db.file_system.read_context import FileSystemDBReadContext
from cellstar_db.file_system.volume_and_segmentation_context import (
    VolumeAndSegmentationContext,
)
from cellstar_db.models import AnnotationsMetadata, Metadata, VolumeMetadata
from cellstar_db.protocol import DBReadContext, VolumeServerDB


class FileSystemVolumeServerDB(VolumeServerDB):
    async def list_sources(self) -> list[str]:
        sources: list[str] = []
        for file in os.listdir(self.folder):
            d = os.path.join(self.folder, file)
            if os.path.isdir(d):
                if (
                    file == "interface"
                    or file == "implementations"
                    or file.startswith("_")
                ):
                    continue

                sources.append(str(file))

        return sources

    async def list_entries(self, source: str, limit: int) -> list[str]:
        entries: list[str] = []
        source_path = os.path.join(self.folder, source)
        for file in os.listdir(source_path):
            entries.append(file)
            limit -= 1
            if limit == 0:
                break

        return entries

    def __init__(self, folder: Path, store_type: str = "zip"):
        # either create of say it doesn't exist
        if not folder.is_dir():
            folder.mkdir(parents=True, exist_ok=True)

        self.folder = folder
        self.filenames_to_be_stored = [
            GRID_METADATA_FILENAME,
            ANNOTATION_METADATA_FILENAME,
            GEOMETRIC_SEGMENTATION_FILENAME,
        ]

        if not store_type in ["directory", "zip"]:
            raise ArgumentError(f"store type is not supported: {store_type}")

        self.store_type = store_type

    def _path_to_object(self, namespace: str, key: str) -> Path:
        """
        Returns path to DB entry based on namespace and key
        """
        return self.folder / namespace / key

    def path_to_zarr_root_data(self, namespace: str, key: str) -> Path:
        """
        Returns path to actual zarr structure root depending on store type
        """
        if self.store_type == "directory":
            return self._path_to_object(namespace=namespace, key=key)
        elif self.store_type == "zip":
            return (
                self._path_to_object(namespace=namespace, key=key)
                / ZIP_STORE_DATA_ZIP_NAME
            )
        else:
            raise ValueError(f"store type is not supported: {self.store_type}")

    async def contains(self, namespace: str, key: str) -> bool:
        """
        Checks if DB entry exists
        """
        return self._path_to_object(namespace, key).is_dir()

    async def delete(self, namespace: str, key: str):
        """
        Removes entry
        """
        path = self._path_to_object(namespace=namespace, key=key)
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        else:
            raise Exception(f"Entry path {path} does not exists or is not a dir")

    def remove_all_entries(self):
        """
        Removes all entries from db
        used before another run of building db to build it from scratch without interfering with
        previously existing entries
        """
        for namespace in DB_NAMESPACES:
            content = sorted((self.folder / namespace).glob("*"))
            for path in content:
                if path.is_file():
                    path.unlink()
                if path.is_dir():
                    shutil.rmtree(path, ignore_errors=True)

    async def add_custom_annotations(
        self, namespace: str, key: str, temp_store_path: Path
    ) -> bool:
        """
        Takes path to temp zarr structure returned by preprocessor as argument
        """
        # Storing as a file (ZIP, bzip2 compression)
        # Compression constants for compression arg of ZipStore()
        # ZIP_STORED = 0
        # ZIP_DEFLATED = 8 (zlib)
        # ZIP_BZIP2 = 12
        # ZIP_LZMA = 1
        # close store after writing, or use 'with' https://zarr.readthedocs.io/en/stable/api/storage.html#zarr.storage.ZipStore
        temp_store: zarr.storage.DirectoryStore = zarr.DirectoryStore(
            str(temp_store_path)
        )
        if (temp_store_path / ANNOTATION_METADATA_FILENAME).exists():
            shutil.copy2(
                temp_store_path / ANNOTATION_METADATA_FILENAME,
                self._path_to_object(namespace, key) / ANNOTATION_METADATA_FILENAME,
            )
        else:
            print("no annotation metadata file found, continuing without copying it")

        temp_store.rmdir()
        # TODO: check if copied and store closed properly
        return True

    def store_entry_files(self, temp_store_path: Path, namespace: str, key: str):
        for filename in self.filenames_to_be_stored:
            self._store_entry_file(
                temp_store_path=temp_store_path,
                filename=filename,
                namespace=namespace,
                key=key,
            )

    def _store_entry_file(
        self, temp_store_path: Path, filename: str, namespace: str, key: str
    ):
        if (temp_store_path / filename).exists():
            shutil.copy2(
                temp_store_path / filename,
                self._path_to_object(namespace, key) / filename,
            )
        else:
            print(f"no {filename} file found, continuing without copying it")

    async def add_segmentation_to_entry(
        self, namespace: str, key: str, temp_store_path: Path
    ) -> bool:
        """
        Takes path to temp zarr structure returned by preprocessor as argument
        """
        # Storing as a file (ZIP, bzip2 compression)
        # Compression constants for compression arg of ZipStore()
        # ZIP_STORED = 0
        # ZIP_DEFLATED = 8 (zlib)
        # ZIP_BZIP2 = 12
        # ZIP_LZMA = 1
        # close store after writing, or use 'with' https://zarr.readthedocs.io/en/stable/api/storage.html#zarr.storage.ZipStore
        temp_store: zarr.storage.DirectoryStore = zarr.DirectoryStore(
            str(temp_store_path)
        )

        # WHAT NEEDS TO BE CHANGED
        # perm_store = zarr.ZipStore(self._path_to_object(namespace, key) + '.zip', mode='w', compression=12)

        # plan:
        # open existing store using open_zarr_zip in reading mode
        # copy data from it to temp store with segmentation
        # store.rmdir()
        # open zip store again for writing
        # copy_store from temp store to perm zip store

        if self.store_type == "zip":
            existing_store = zarr.ZipStore(
                path=str(self.path_to_zarr_root_data(namespace, key)),
                compression=0,
                allowZip64=True,
                mode="r",
            )
            # Re-create zarr hierarchy from opened store
            existing_root: zarr.Group = zarr.group(store=existing_store)

            # copy data from existing to temp store
            zarr.copy_store(
                source=existing_store,
                dest=temp_store,
                source_path=VOLUME_DATA_GROUPNAME,
                dest_path=VOLUME_DATA_GROUPNAME,
            )

            existing_store.close()

            # remove existing store
            # TODO: find a better way to remove it
            self.path_to_zarr_root_data(namespace, key).unlink()

            # create it again
            perm_store = zarr.ZipStore(
                path=str(self.path_to_zarr_root_data(namespace, key)),
                compression=0,
                allowZip64=True,
                mode="w",
            )
            zarr.copy_store(temp_store, perm_store)  # , log=stdout)

        else:
            raise ArgumentError("store type is wrong: {self.store_type}")

        # PART BELOW WILL STAY AS IT IS probably
        print("A: " + str(temp_store_path))
        print("B: " + GRID_METADATA_FILENAME)

        self.store_entry_files(
            temp_store_path=temp_store_path, namespace=namespace, key=key
        )

        if self.store_type == "zip":
            perm_store.close()

        temp_store.rmdir()
        # TODO: check if copied and store closed properly
        return True

    async def store(self, namespace: str, key: str, temp_store_path: Path) -> bool:
        """
        Takes path to temp zarr structure returned by preprocessor as argument
        """
        # Storing as a file (ZIP, bzip2 compression)
        # Compression constants for compression arg of ZipStore()
        # ZIP_STORED = 0
        # ZIP_DEFLATED = 8 (zlib)
        # ZIP_BZIP2 = 12
        # ZIP_LZMA = 1
        # close store after writing, or use 'with' https://zarr.readthedocs.io/en/stable/api/storage.html#zarr.storage.ZipStore
        temp_store: zarr.storage.DirectoryStore = zarr.DirectoryStore(
            str(temp_store_path)
        )

        # WHAT NEEDS TO BE CHANGED
        # perm_store = zarr.ZipStore(self._path_to_object(namespace, key) + '.zip', mode='w', compression=12)

        if self.store_type == "directory":
            perm_store = zarr.DirectoryStore(str(self._path_to_object(namespace, key)))
            zarr.copy_store(temp_store, perm_store)  # , log=stdout)
        elif self.store_type == "zip":
            entry_dir_path = self._path_to_object(namespace, key)
            entry_dir_path.mkdir(parents=True, exist_ok=True)
            perm_store = zarr.ZipStore(
                path=str(self.path_to_zarr_root_data(namespace, key)),
                compression=0,
                allowZip64=True,
                mode="w",
            )
            zarr.copy_store(temp_store, perm_store)  # , log=stdout)
        else:
            raise ArgumentError("store type is wrong: {self.store_type}")

        # PART BELOW WILL STAY AS IT IS probably
        print("A: " + str(temp_store_path))
        print("B: " + GRID_METADATA_FILENAME)

        self.store_entry_files(
            temp_store_path=temp_store_path, namespace=namespace, key=key
        )

        if self.store_type == "zip":
            perm_store.close()

        temp_store.rmdir()
        # TODO: check if copied and store closed properly
        return True

    def read(self, namespace: str, key: str) -> DBReadContext:
        return FileSystemDBReadContext(db=self, namespace=namespace, key=key)

    def edit_data(
        self, namespace: str, key: str, working_folder: Path
    ) -> VolumeAndSegmentationContext:
        return VolumeAndSegmentationContext(
            db=self, namespace=namespace, key=key, working_folder=working_folder
        )

    def edit_annotations(self, namespace: str, key: str) -> AnnnotationsEditContext:
        return AnnnotationsEditContext(db=self, namespace=namespace, key=key)

    async def read_metadata(self, namespace: str, key: str) -> VolumeMetadata:
        path: Path = (
            self._path_to_object(namespace=namespace, key=key) / GRID_METADATA_FILENAME
        )
        with open(path.resolve(), "r", encoding="utf-8") as f:
            # reads into dict
            read_json_of_metadata: Metadata = Metadata.parse_file(f)
        return FileSystemVolumeMedatada(read_json_of_metadata)

    async def read_annotations(self, namespace: str, key: str) -> AnnotationsMetadata:
        path: Path = (
            self._path_to_object(namespace=namespace, key=key)
            / ANNOTATION_METADATA_FILENAME
        )
        with open(path.resolve(), "r", encoding="utf-8") as f:
            # reads into dict
            read_json_of_metadata: AnnotationsMetadata = json.load(f)
        return read_json_of_metadata
