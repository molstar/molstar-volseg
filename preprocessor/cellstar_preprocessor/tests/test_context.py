import shutil
from pathlib import Path

from cellstar_db.models import InputKind
import zarr
from cellstar_preprocessor.flows.constants import (
    INIT_ANNOTATIONS_MODEL,
    INIT_METADATA_MODEL,
)
from cellstar_preprocessor.tests.helper_methods import (
    download_map_for_tests,
    download_omezarr_for_tests,
    download_sff_for_tests,
)
from cellstar_preprocessor.tests.input_for_tests import TestInput


class TestContext:
    __test__ = False
    def _download_input(self):
        # TODO: extract omezarr annotations require segmentations
        p: Path
        if self.test_input.kind == InputKind.sff:
            p = download_sff_for_tests(self.test_input.url)
        elif self.test_input.kind == InputKind.omezarr:
            p = download_omezarr_for_tests(self.test_input.url)
        elif self.test_input.kind == InputKind.map:
            p = download_map_for_tests(self.test_input.url)

        self.test_file_path = p

    def _remove_input(self):
        if self.test_file_path.exists():
            # if self.test_file_path.is_file():
            #     self.test_file_path.unlink()
            # else:
            shutil.rmtree(self.test_file_path.parent)

    def _init_zarr_structure(self):
        # if self.working_folder.exists():
        #     shutil.rmtree(self.working_folder, ignore_errors=True)
        self.intermediate_zarr_structure_path = (
            self.working_folder / self.test_input.entry_id
        )
        store: zarr.storage.DirectoryStore = zarr.DirectoryStore(
            str(self.intermediate_zarr_structure_path)
        )
        root = zarr.group(store=store)

        root.attrs["metadata_dict"] = INIT_METADATA_MODEL.dict()
        root.attrs["annotations_dict"] = INIT_ANNOTATIONS_MODEL.dict()
        self.root = root
        self.store = store

    def _remove_zarr_structure(self):
        if self.intermediate_zarr_structure_path.exists():
            shutil.rmtree(self.intermediate_zarr_structure_path)

    def __enter__(self):
        # init zarr structure
        self._init_zarr_structure()
        self._download_input()

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if hasattr(self.store, "close"):
            self.store.close()
        else:
            pass

        self._remove_input()
        self._remove_zarr_structure()

    async def __aenter__(self):
        self._init_zarr_structure()
        return self

    async def __aexit__(self, *args, **kwargs):
        if hasattr(self.store, "aclose"):
            await self.store.aclose()
        if hasattr(self.store, "close"):
            self.store.close()
        else:
            pass

        self._remove_input()
        self._remove_zarr_structure()

    def __init__(
        self,
        test_input: TestInput,
        working_folder: Path,
    ):
        self.test_input = test_input
        self.working_folder = working_folder
        self.intermediate_zarr_structure_path: Path | None = None
        self.test_file_path: Path | None = None
        self.root: zarr.Group | None = None
        self.store: zarr.DirectoryStore | None = None


def context_for_tests(test_input: TestInput, working_folder: Path) -> TestContext:
    return TestContext(test_input, working_folder)
