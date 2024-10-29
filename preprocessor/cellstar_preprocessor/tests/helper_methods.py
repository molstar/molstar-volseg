import shutil
import urllib.request
from pathlib import Path
from uuid import uuid4

import ome_zarr
import ome_zarr.utils
import zarr
from cellstar_db.models import (
    DataKind,
    DownsamplingParams,
    EntryData,
    AssetKind,
    QuantizationDtype,
    AssetSourceInfo,
    StoringParams,
)
from cellstar_preprocessor.flows.constants import (
    ANNOTATIONS_DICT_NAME,
    INIT_ANNOTATIONS_MODEL,
    INIT_METADATA_MODEL,
    METADATA_DICT_NAME,
)
from cellstar_preprocessor.model.segmentation import InternalSegmentation
from cellstar_preprocessor.model.volume import InternalVolume
from cellstar_preprocessor.tests.input_for_tests import (
    PATH_TO_INPUTS_FOR_TESTS,
    TEST_MAP_PATH_XYZ_ORDER,
    TEST_MAP_PATH_ZYX_ORDER,
    WORKING_FOLDER_FOR_TESTS,
    TestInput,
)
from cellstar_preprocessor.tools.gunzip.gunzip import gunzip


def remove_intermediate_zarr_structure_for_tests(p: Path):
    # p = WORKING_FOLDER_FOR_TESTS / unique_folder_name
    if p.exists():
        shutil.rmtree(p, ignore_errors=True)


def get_internal_XYZ_volume(intermediate_zarr_structure_for_tests: Path):
    return InternalVolume(
        path=intermediate_zarr_structure_for_tests,
        input_path=TEST_MAP_PATH_XYZ_ORDER,
        params_for_storing=StoringParams(),
        volume_force_dtype="f2",
        downsampling_parameters=DownsamplingParams(),
        entry_data=EntryData(
            entry_id="emd-555555",
            source_db="emdb",
            source_db_id="emd-555555",
            source_db_name="emdb",
        ),
        quantize_dtype_str=QuantizationDtype.u1,
        quantize_downsampling_levels=(1,),
        input_kind=AssetKind.map,
    )


def get_internal_ZYX_volume(intermediate_zarr_structure_for_tests: Path):
    return InternalVolume(
        path=intermediate_zarr_structure_for_tests,
        input_path=TEST_MAP_PATH_ZYX_ORDER,
        params_for_storing=StoringParams(),
        volume_force_dtype="f2",
        downsampling_parameters=DownsamplingParams(),
        entry_data=EntryData(
            entry_id="emd-555555",
            source_db="emdb",
            source_db_id="emd-555555",
            source_db_name="emdb",
        ),
        quantize_dtype_str=QuantizationDtype.u1,
        quantize_downsampling_levels=(1,),
        input_kind=AssetKind.map,
    )


def initialize_intermediate_zarr_structure_for_tests(unique_folder_name: str):
    p = WORKING_FOLDER_FOR_TESTS / unique_folder_name
    if p.exists():
        shutil.rmtree(p, ignore_errors=True)

    store: zarr.storage.DirectoryStore = zarr.DirectoryStore(str(p))
    root = zarr.group(store=store)

    root.attrs[METADATA_DICT_NAME] = INIT_METADATA_MODEL.model_dump()
    root.attrs[ANNOTATIONS_DICT_NAME] = INIT_ANNOTATIONS_MODEL.model_dump()
    return p


def get_internal_segmentation(
    t: TestInput, segmentation_path: Path, intermediate_zarr_structure: Path
):
    internal_segmentation = InternalSegmentation(
        path=intermediate_zarr_structure,
        input_path=segmentation_path,
        params_for_storing=StoringParams(),
        downsampling_parameters=DownsamplingParams(),
        entry_data=EntryData(
            entry_id=t.entry_id,
            source_db=t.source_db,
            source_db_id=t.entry_id,
            source_db_name=t.source_db,
        ),
        input_kind=t.asset_info.kind,
        data_kind=DataKind.segmentation
    )
    return internal_segmentation

# def get_internal_segmentation(
#     t: TestInput, segmentation_path: Path, intermediate_zarr_structure: Path
# ):
#     # p = _download_sff_for_tests(test_input['url'])
#     internal_segmentation = InternalSegmentation(
#         path=intermediate_zarr_structure,
#         input_path=segmentation_path,
#         params_for_storing=StoringParams(),
#         downsampling_parameters=DownsamplingParams(),
#         entry_data=EntryData(
#             entry_id=t.entry_id,
#             source_db=t.source_db,
#             source_db_id=t.entry_id,
#             source_db_name=t.source_db,
#         ),
#         input_kind=AssetKind.sff,
#     )
#     return internal_segmentation


def get_internal_volume_from_input(
    test_input: TestInput, volume_path: Path, intermediate_zarr_structure: Path
):
    # if test_input.asset_info.kind in [AssetKind.ometiff_image, AssetKind.]
    # p = download_omezarr_for_tests(omezar_test_input['url'])
    internal_volume = InternalVolume(
        path=intermediate_zarr_structure,
        input_path=volume_path,
        params_for_storing=StoringParams(),
        volume_force_dtype=None,
        downsampling_parameters=DownsamplingParams(),
        entry_data=EntryData(
            entry_id=test_input.entry_id,
            source_db=test_input.source_db,
            source_db_id=test_input.entry_id,
            source_db_name=test_input.source_db,
        ),
        quantize_dtype_str=None,
        quantize_downsampling_levels=None,
        input_kind=test_input.asset_info.kind,
        data_kind=DataKind.volume
    )
    return internal_volume


# def get_omezarr_internal_segmentation(
#     omezar_test_input: TestInput,
#     segmentation_path: Path,
#     intermediate_zarr_structure: Path,
# ):
#     # p = download_omezarr_for_tests(omezar_test_input['url'])
#     internal_segmentation = InternalSegmentation(
#         path=intermediate_zarr_structure,
#         input_path=segmentation_path,
#         params_for_storing=StoringParams(),
#         downsampling_parameters=DownsamplingParams(),
#         entry_data=EntryData(
#             entry_id=omezar_test_input.entry_id,
#             source_db=omezar_test_input.source_db,
#             source_db_id=omezar_test_input.entry_id,
#             source_db_name=omezar_test_input.source_db,
#         ),
#         input_kind=AssetKind.omezarr,
#     )
#     return internal_segmentation


# def get_sff_for_tests(resource: AssetResourceInfo):
#     sff_gz_name = url.split("/")[-1]
#     # gunzip
#     unique_name = str(uuid4())
#     unique_dir = PATH_TO_INPUTS_FOR_TESTS / unique_name
#     if unique_dir.exists():
#         shutil.rmtree(unique_dir)
#     unique_dir.mkdir(parents=True)

#     sff_gz_path = unique_dir / sff_gz_name

#     urllib.request.urlretrieve(url, str(sff_gz_path.resolve()))
#     sff_path = gunzip(sff_gz_path)
#     return sff_path


# def get_map_for_tests(resource: AssetResourceInfo):
#     map_gz_name = url.split("/")[-1]
#     # gunzip
#     unique_name = str(uuid4())
#     unique_dir = PATH_TO_INPUTS_FOR_TESTS / unique_name
#     if unique_dir.exists():
#         shutil.rmtree(unique_dir)
#     unique_dir.mkdir(parents=True)

#     map_gz_path = unique_dir / map_gz_name
#     urllib.request.urlretrieve(url, str(map_gz_path.resolve()))
#     map_path = gunzip(map_gz_path)
#     return map_path


# def get_omezarr_for_tests(resource: AssetResourceInfo):
#     # wrong
#     omezarr_name = url.split("/")[-1]
#     unique_name = str(uuid4())
#     # omezarr_unique_subfolder = PATH_TO_TEST_DATA_DIR / unique_subfolder
#     unique_dir = PATH_TO_INPUTS_FOR_TESTS / unique_name
#     if unique_dir.exists():
#         shutil.rmtree(unique_dir)
#     unique_dir.mkdir(parents=True)
#     omezarr_path = unique_dir / omezarr_name
#     if not omezarr_path.exists():
#         # shutil.rmtree(omezarr_path)
#         # get omezarr_path here
#         ome_zarr.utils.download(url, str(unique_dir.resolve()))
#     return omezarr_path
