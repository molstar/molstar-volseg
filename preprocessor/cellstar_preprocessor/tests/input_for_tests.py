from pathlib import Path

from attr import dataclass
from cellstar_db.models import (
    CompressionFormat,
    DataKind,
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
            source=AssetSourceInfo(kind="external", uri="https://www.ebi.ac.uk/em_static/emdb_sff/empiar_10070_b3talongmusc20130301/empiar_10070_b3talongmusc20130301.hff.gz", compression=CompressionFormat.hff_gzipped_file),
            ),
        entry_id="empiar-10070",
        source_db="empiar",
    ),
    TestInput(
        asset_info=AssetInfo(
            kind=AssetKind.sff,
            source=AssetSourceInfo(kind="external", uri="https://www.ebi.ac.uk/em_static/emdb_sff/18/1832/emd_1832.hff.gz", compression=CompressionFormat.gzipped_file)
            ),
        entry_id="emd-1832",
        source_db="emdb",
    ),
]

MASK_SEGMENTATION_TEST_INPUTS = [
    TestInput(
        asset_info=AssetInfo(
            kind=AssetKind.ometiff_image,
            source=AssetSourceInfo(kind="external", uri="https://ftp.ebi.ac.uk/pub/databases/emdb/structures/EMD-1273/masks/emd_1273_msk_5.map")
            ),
        entry_id="emd-1273",
        source_db="emdb",
    )
]

TIFF_IMAGE_STACK_DIR_TEST_INPUTS = [
    TestInput(
        asset_info=AssetInfo(
            kind=AssetKind.tiff_image_stack_dir,
            source=AssetSourceInfo(kind="external", uri="https://ftp.ebi.ac.uk/empiar/world_availability/12017/data/Obese%20LacZ/ob_LacZ_2679_mitochondria-instance_32-bit.zip")
            ),
        entry_id="empiar-12017",
        source_db="empiar",
    )
]

# TODO: TIFF SEGMENTATION STACK DIR
# TIFF_IMAGE_STACK_DIR_TEST_INPUTS = [
#     TestInput(
#         asset_info=AssetInfo(
#             kind=AssetKind.tiff_image_stack_dir,
#             source=AssetSourceInfo(kind="external", uri="https://ftp.ebi.ac.uk/empiar/world_availability/12017/data/Obese%20LacZ/ob_LacZ_2679_mitochondria-instance_32-bit.zip")
#             ),
#         entry_id="empiar-12017",
#         source_db="empiar",
#     )
# ]

OMETIFF_SEGMENTATION_TEST_INPUTS = [
    TestInput(
        asset_info=AssetInfo(
            kind=AssetKind.ometiff_segmentation,
            source=AssetSourceInfo(kind="external", uri="https://allencell.s3.amazonaws.com/aics/hipsc_single_cell_image_dataset/crop_seg/a9a2aa179450b1819f0dfc4d22411e6226f22e3c88f7a6c3f593d0c2599c2529_segmentation.ome.tif")
            ),
        entry_id="custom-tubhiswt",
        source_db="custom",
    )
]

OMETIFF_IMAGE_TEST_INPUTS = [
    TestInput(
        asset_info=AssetInfo(
            kind=AssetKind.ometiff_image,
            source=AssetSourceInfo(kind="external", uri="https://allencell.s3.amazonaws.com/aics/hipsc_single_cell_image_dataset/crop_raw/7922e74b69b77d6b51ea5f1627418397ab6007105a780913663ce1344905db5c_raw.ome.tif")
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

INTERNAL_LATTICE_SEGMENTATION_FOR_TESTING = InternalSegmentation(
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
    data_kind=DataKind.segmentation
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
    data_kind=DataKind.segmentation
)
