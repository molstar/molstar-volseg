import shutil
import urllib.request
from pathlib import Path
from uuid import uuid4

import ome_zarr
import ome_zarr.utils
import zarr
from cellstar_preprocessor.flows.constants import (
    INIT_ANNOTATIONS_DICT,
    INIT_METADATA_DICT,
)
from cellstar_preprocessor.model.input import (
    DownsamplingParams,
    EntryData,
    QuantizationDtype,
    StoringParams,
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
        intermediate_zarr_structure_path=intermediate_zarr_structure_for_tests,
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
    )


def get_internal_ZYX_volume(intermediate_zarr_structure_for_tests: Path):
    return InternalVolume(
        intermediate_zarr_structure_path=intermediate_zarr_structure_for_tests,
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
    )


def initialize_intermediate_zarr_structure_for_tests(unique_folder_name: str):
    p = WORKING_FOLDER_FOR_TESTS / unique_folder_name
    if p.exists():
        shutil.rmtree(p, ignore_errors=True)

    store: zarr.storage.DirectoryStore = zarr.DirectoryStore(str(p))
    root = zarr.group(store=store)

    root.attrs["metadata_dict"] = INIT_METADATA_DICT
    root.attrs["annotations_dict"] = INIT_ANNOTATIONS_DICT
    return p


def get_sff_internal_segmentation(
    test_input: TestInput, segmentation_path: Path, intermediate_zarr_structure: Path
):
    # p = _download_sff_for_tests(test_input['url'])
    internal_segmentation = InternalSegmentation(
        intermediate_zarr_structure_path=intermediate_zarr_structure,
        input_path=segmentation_path,
        params_for_storing=StoringParams(),
        downsampling_parameters=DownsamplingParams(),
        entry_data=EntryData(
            entry_id=test_input["entry_id"],
            source_db=test_input["source_db"],
            source_db_id=test_input["entry_id"],
            source_db_name=test_input["source_db"],
        ),
    )
    return internal_segmentation


def get_internal_volume_from_input(
    test_input: TestInput, volume_path: Path, intermediate_zarr_structure: Path
):
    # p = download_omezarr_for_tests(omezar_test_input['url'])
    internal_volume = InternalVolume(
        intermediate_zarr_structure_path=intermediate_zarr_structure,
        input_path=volume_path,
        params_for_storing=StoringParams(),
        volume_force_dtype=None,
        downsampling_parameters=DownsamplingParams(),
        entry_data=EntryData(
            entry_id=test_input["entry_id"],
            source_db=test_input["source_db"],
            source_db_id=test_input["entry_id"],
            source_db_name=test_input["source_db"],
        ),
        quantize_dtype_str=None,
        quantize_downsampling_levels=None,
    )
    return internal_volume


def get_omezarr_internal_segmentation(
    omezar_test_input: TestInput,
    segmentation_path: Path,
    intermediate_zarr_structure: Path,
):
    # p = download_omezarr_for_tests(omezar_test_input['url'])
    internal_segmentation = InternalSegmentation(
        intermediate_zarr_structure_path=intermediate_zarr_structure,
        input_path=segmentation_path,
        params_for_storing=StoringParams(),
        downsampling_parameters=DownsamplingParams(),
        entry_data=EntryData(
            entry_id=omezar_test_input["entry_id"],
            source_db=omezar_test_input["source_db"],
            source_db_id=omezar_test_input["entry_id"],
            source_db_name=omezar_test_input["source_db"],
        ),
    )
    return internal_segmentation


def download_sff_for_tests(url: str):
    sff_gz_name = url.split("/")[-1]
    # gunzip
    unique_name = str(uuid4())
    unique_dir = PATH_TO_INPUTS_FOR_TESTS / unique_name
    if unique_dir.exists():
        shutil.rmtree(unique_dir)
    unique_dir.mkdir(parents=True)

    sff_gz_path = unique_dir / sff_gz_name

    urllib.request.urlretrieve(url, str(sff_gz_path.resolve()))
    sff_path = gunzip(sff_gz_path)
    return sff_path


def download_map_for_tests(url: str):
    map_gz_name = url.split("/")[-1]
    # gunzip
    unique_name = str(uuid4())
    unique_dir = PATH_TO_INPUTS_FOR_TESTS / unique_name
    if unique_dir.exists():
        shutil.rmtree(unique_dir)
    unique_dir.mkdir(parents=True)

    map_gz_path = unique_dir / map_gz_name
    urllib.request.urlretrieve(url, str(map_gz_path.resolve()))
    map_path = gunzip(map_gz_path)
    return map_path


def download_omezarr_for_tests(url: str):
    # wrong
    omezarr_name = url.split("/")[-1]
    unique_name = str(uuid4())
    # omezarr_unique_subfolder = PATH_TO_TEST_DATA_DIR / unique_subfolder
    unique_dir = PATH_TO_INPUTS_FOR_TESTS / unique_name
    if unique_dir.exists():
        shutil.rmtree(unique_dir)
    unique_dir.mkdir(parents=True)
    omezarr_path = unique_dir / omezarr_name
    if not omezarr_path.exists():
        # shutil.rmtree(omezarr_path)
        # get omezarr_path here
        ome_zarr.utils.download(url, str(unique_dir.resolve()))
    return omezarr_path
