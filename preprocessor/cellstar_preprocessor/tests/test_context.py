import shutil
from pathlib import Path
from uuid import uuid4

from cellstar_preprocessor.tools.asset_getter.asset_getter import AssetGetter
from cellstar_preprocessor.tools.clean_url.clean_url import clean_url
from cellstar_preprocessor.tools.remove_path.remove_path import remove_path
import zarr
from cellstar_db.models import AssetKind, CompressionFormat, SourceKind
from cellstar_preprocessor.flows.constants import (
    ANNOTATIONS_DICT_NAME,
    INIT_ANNOTATIONS_MODEL,
    INIT_METADATA_MODEL,
    METADATA_DICT_NAME,
)
from cellstar_preprocessor.tests.input_for_tests import PATH_TO_INPUTS_FOR_TESTS, TestInput


class TestContext:
    def __init__(
        self,
        test_input: TestInput,
        working_folder: Path,
    ):
        self.test_input = test_input
        self.working_folder: Path = working_folder
        self.test_input_asset_path: Path | None = None
        self.root: zarr.Group | None = None
        self.store: zarr.DirectoryStore | None = None
        
    __test__ = False
    
    def __create_input_path(self):
        # TODO: handle URLs with ? here
        # create unique name
        unique_dir_name = str(uuid4())
        unique_dir = PATH_TO_INPUTS_FOR_TESTS / unique_dir_name
        if unique_dir.exists():
            shutil.rmtree(unique_dir)
        unique_dir.mkdir(parents=True)
        # get if from asset, e.g. resource name 
        name = self.test_input.asset_info.source.name
        if self.test_input.asset_info.source.kind == SourceKind.external:
            name = clean_url(name)
        if self.test_input.asset_info.source.compression in {CompressionFormat.zip_dir, CompressionFormat.hff_gzipped_file, CompressionFormat.map_gzipped_file, CompressionFormat.gzipped_file}:            
            # for zip - folder name
            # for hff gz = .hff file name
            # for map gz = .map file name
            # for generic gz = .xxx file name
            name = self.test_input.asset_info.source.stem
            
        
        output_path = unique_dir / name
        return output_path
        # as a result create dir with unique name for input
    
    def _get_input(self):
        self.test_input_asset_path = self.__create_input_path()
        # self.test_input_asset_path should be without gz suffix
        g = AssetGetter(self.test_input.asset_info, self.test_input_asset_path)
        target_path = g.get_asset()
        if target_path.resolve() != self.test_input_asset_path.resolve():
            print(f'test_input_asset_path set to target_path ')
            # exists at that point
            self.test_input_asset_path = target_path
        
        # if self.test_input.kind == AssetKind.sff:
        #     p = get_sff_for_tests(self.test_input.resource)
        # elif self.test_input.kind == AssetKind.omezarr:
        #     p = get_omezarr_for_tests(self.test_input.resource)
        # elif self.test_input.kind == AssetKind.map:
        #     p = get_map_for_tests(self.test_input.resource)

        # self.test_file_path = p

    def _remove_test_input_asset(self):
        '''Remove folder in which test input file is stored'''
        remove_path(self.test_input_asset_path.parent)
        # if self.test_file_path.exists():
        #     # if self.test_file_path.is_file():
        #     #     self.test_file_path.unlink()
        #     # else:
        #     shutil.rmtree(self.test_file_path.parent)

    def _init_zarr_structure(self):
        # if self.working_folder.exists():
        #     shutil.rmtree(self.working_folder, ignore_errors=True)
        self.working_folder = (
            self.working_folder / self.test_input.entry_id
        )
        store: zarr.storage.DirectoryStore = zarr.DirectoryStore(
            str(self.working_folder)
        )
        root = zarr.group(store=store)

        root.attrs[METADATA_DICT_NAME] = INIT_METADATA_MODEL.model_dump()
        root.attrs[ANNOTATIONS_DICT_NAME] = INIT_ANNOTATIONS_MODEL.model_dump()
        self.root = root
        self.store = store

    def _remove_zarr_structure(self):
        if self.working_folder.exists():
            shutil.rmtree(self.working_folder)

    def __enter__(self):
        # init zarr structure
        self._init_zarr_structure()
        self._get_input()

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if hasattr(self.store, "close"):
            self.store.close()
        else:
            pass

        self._remove_test_input_asset()
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

        self._remove_test_input_asset()
        self._remove_zarr_structure()

def context_for_tests(test_input: TestInput, working_folder: Path) -> TestContext:
    return TestContext(test_input, working_folder)
