from pathlib import Path

from attr import dataclass
from cellstar_db.models import (
    CompressionFormat,
    DownsamplingParams,
    EntryData,
    AssetKind,
    QuantizationDtype,
    AssetInfo,
    AssetSourceInfo,
    StoringParams,
)
from cellstar_preprocessor.model.segmentation import InternalSegmentation
from cellstar_preprocessor.model.volume import InternalVolume

WORKING_FOLDER_FOR_TESTS = Path(
    "preprocessor/cellstar_preprocessor/tests/test_data/working_folder"
)

PATH_TO_TEST_DATA_DIR: Path = Path("preprocessor/cellstar_preprocessor/tests/test_data")
PATH_TO_INPUTS_FOR_TESTS: Path = PATH_TO_TEST_DATA_DIR / "inputs_for_tests"

TEST_MAP_PATH = Path("test-data/preprocessor/sample_volumes/emdb_sff/EMD-1832.map")
TEST_SFF_PATH = Path(
    "test-data/preprocessor/sample_segmentations/emdb_sff/emd_1832.hff"
)
TEST_MESH_SFF_PATH = Path(
    "test-data/preprocessor/sample_segmentations/empiar/empiar_10070_b3talongmusc20130301.hff"
)
TEST_MAP_PATH_ZYX_ORDER = Path(
    "preprocessor/cellstar_preprocessor/tests/test_data/fake_ccp4_ZYX.map"
)
TEST_MAP_PATH_XYZ_ORDER = Path(
    "preprocessor/cellstar_preprocessor/tests/test_data/fake_ccp4_XYZ.map"
)


@dataclass
class TestInput:
    asset_info: AssetInfo
    # output_path
    entry_id: str
    source_db: str
    __test__ = False

# TODO: TRY to somehow unify with database downloading functions

MAP_TEST_INPUTS = [
    TestInput(
        asset_info=AssetInfo(
            kind=AssetKind.map,
            source=AssetSourceInfo(kind="local", uri=str(TEST_MAP_PATH_XYZ_ORDER.resolve()))
            ),
        entry_id="custom-XYZ",
        source_db="custom",
    ),
    TestInput(
        asset_info=AssetInfo(
            kind=AssetKind.map,
            source=AssetSourceInfo(kind="local", uri=str(TEST_MAP_PATH_ZYX_ORDER.resolve()))
            ),
        entry_id="custom-ZYX",
        source_db="custom",
    )
]

SFF_TEST_INPUTS = [
    TestInput(
        asset_info=AssetInfo(
            kind=AssetKind.sff,
            source=AssetSourceInfo(kind="external", uri="https://www.ebi.ac.uk/em_static/emdb_sff/empiar_10070_b3talongmusc20130301/empiar_10070_b3talongmusc20130301.hff.gz")
            ),
        entry_id="empiar-10070",
        source_db="empiar",
    ),
    TestInput(
        asset_info=AssetInfo(
            kind=AssetKind.sff,
            source=AssetSourceInfo(kind="external", uri="https://www.ebi.ac.uk/em_static/emdb_sff/18/1832/emd_1832.hff.gz")
            ),
        entry_id="emd-1832",
        source_db="emdb",
    ),
]

OMETIFF_IMAGE_TEST_INPUTS = [
    TestInput(
        asset_info=AssetInfo(
            kind=AssetKind.ometiff_image,
            # source=AssetSourceInfo(kind="external", uri="https://allencell.s3.amazonaws.com/aics/hipsc_single_cell_image_dataset/crop_raw/00011451c65b106cf9889bbf78cb4aa2cf2f9ec56c681e50fafc9635c3abf752_raw.ome.tif?versionId=T5RJhnjG9tczKyxKVkc_GpcF7sLkg4bm")
            source=AssetSourceInfo(kind="external", uri="https://allencell.s3.amazonaws.com/aics/hipsc_single_cell_image_dataset/crop_raw/00011451c65b106cf9889bbf78cb4aa2cf2f9ec56c681e50fafc9635c3abf752_raw.ome.tif")
            ),
        entry_id="custom-tubhiswt",
        source_db="custom",
    )
    # TestInput(
    #     asset_info=AssetInfo(
    #         kind=AssetKind.ometiff_image,
    #         source=AssetSourceInfo(kind="external", compression=CompressionFormat.zip_archive, uri="https://downloads.openmicroscopy.org/images/OME-TIFF/2016-06/tubhiswt-4D.zip")
    #         ),
    #     entry_id="custom-tubhiswt",
    #     source_db="custom",
    # ),
]

OMEZARR_TEST_INPUTS = [
    TestInput(
        asset_info=AssetInfo(
            kind=AssetKind.omezarr,
            source=AssetSourceInfo(kind="external", uri="https://uk1s3.embassy.ebi.ac.uk/idr/zarr/v0.4/idr0062A/6001240.zarr")
            ),
        entry_id="idr-6001240",
        source_db="idr",
    ),
    TestInput(
        asset_info=AssetInfo(
            kind=AssetKind.omezarr,
            source=AssetSourceInfo(kind="external", uri="https://uk1s3.embassy.ebi.ac.uk/idr/zarr/v0.4/idr0101A/13457537.zarr")
            ),
        entry_id="idr-13457537",
        source_db="idr",
    ),
]

MAP_INPUTS_FOR_AXES_TESTING = []

INTERNAL_SEGMENTATION_FOR_TESTING = InternalSegmentation(
    path=WORKING_FOLDER_FOR_TESTS,
    input_path=TEST_SFF_PATH,
    params_for_storing=StoringParams(),
    downsampling_parameters=DownsamplingParams(),
    entry_data=EntryData(
        entry_id="emd-1832",
        source_db="emdb",
        source_db_id="emd-1832",
        source_db_name="emdb",
    ),
    input_kind=AssetKind.sff,
)

INTERNAL_MESH_SEGMENTATION_FOR_TESTING = InternalSegmentation(
    path=WORKING_FOLDER_FOR_TESTS,
    input_path=TEST_MESH_SFF_PATH,
    params_for_storing=StoringParams(),
    downsampling_parameters=DownsamplingParams(),
    entry_data=EntryData(
        entry_id="empiar-10070",
        source_db="empiar",
        source_db_id="empiar-10070",
        source_db_name="empiar",
    ),
    input_kind=AssetKind.sff,
)
