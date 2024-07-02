from pathlib import Path

from attr import dataclass
from cellstar_db.models import (
    DownsamplingParams,
    EntryData,
    InputKind,
    QuantizationDtype,
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
    kind: InputKind
    url: str
    entry_id: str
    source_db: str
    __test__ = False


MAP_TEST_INPUTS = [
    TestInput(
        kind=InputKind.map,
        url="https://ftp.ebi.ac.uk/pub/databases/emdb/structures/EMD-1832/map/emd_1832.map.gz",
        entry_id="emd-1832",
        source_db="emdb",
    )
]

SFF_TEST_INPUTS = [
    TestInput(
        kind=InputKind.sff,
        url="https://www.ebi.ac.uk/em_static/emdb_sff/empiar_10070_b3talongmusc20130301/empiar_10070_b3talongmusc20130301.hff.gz",
        entry_id="empiar-10070",
        source_db="empiar",
    ),
    TestInput(
        kind=InputKind.sff,
        url="https://www.ebi.ac.uk/em_static/emdb_sff/18/1832/emd_1832.hff.gz",
        entry_id="emd-1832",
        source_db="emdb",
    ),
]

OMEZARR_TEST_INPUTS = [
    TestInput(
        kind=InputKind.omezarr,
        url="https://uk1s3.embassy.ebi.ac.uk/idr/zarr/v0.4/idr0062A/6001240.zarr",
        entry_id="idr-6001240",
        source_db="idr",
    ),
    TestInput(
        kind=InputKind.omezarr,
        url="https://uk1s3.embassy.ebi.ac.uk/idr/zarr/v0.4/idr0101A/13457537.zarr",
        entry_id="idr-13457537",
        source_db="idr",
    ),
]

MAP_INPUTS_FOR_AXES_TESTING = []

INTERNAL_VOLUME_FOR_TESTING_XYZ_ORDER = InternalVolume(
    path=WORKING_FOLDER_FOR_TESTS,
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
    input_kind=InputKind.map,
)

INTERNAL_VOLUME_FOR_TESTING_ZYX_ORDER = InternalVolume(
    path=WORKING_FOLDER_FOR_TESTS,
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
    input_kind=InputKind.map,
)


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
    input_kind=InputKind.sff,
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
    input_kind=InputKind.sff,
)
