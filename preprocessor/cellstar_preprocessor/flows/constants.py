from pathlib import Path

from cellstar_db.models import (
    AnnotationsMetadata,
    AxisName,
    EntryId,
    GeometricSegmentationsMetadata,
    MeshSegmentationsMetadata,
    Metadata,
    SamplingInfo,
    SegmentationLatticesMetadata,
    SpatialAxisUnit,
    TimeInfo,
    VolumeSamplingInfo,
    VolumesMetadata,
)

TIFF_EXTENSIONS = {'.tiff', '.tif'}

CSV_WITH_ENTRY_IDS_FILE = Path(
    "test-data/preprocessor/db_building_parameters_custom_entries.csv"
)
DEFAULT_DB_PATH = "preprocessor/temp/test_db"
RAW_INPUT_FILES_DIR = "preprocessor/temp/raw_input_files_dir"
DB_BUILDING_PARAMETERS_JSON = "test-data/preprocessor/db_building_parameters.json"
RAW_INPUT_DOWNLOAD_PARAMS_JSON = "test-data/preprocessor/download_raw_input_params.json"
WORKING_FOLDER_PATH = "preprocessor/temp/temp_zarr_hierarchy_storage"
QUANTIZATION_DATA_DICT_ATTR_NAME = "quantization_data_dict"
LATTICE_SEGMENTATION_DATA_GROUPNAME = "lattice_segmentation_data"
MESH_SEGMENTATION_DATA_GROUPNAME = "mesh_segmentation_data"

VOLUME_DATA_GROUPNAME = "volume_data"
VOLUME_DATA_GROUPNAME_COPY = "volume_data_copy"

# TODO: the namespaces should NOT be hardcoded
DB_NAMESPACES = ("emdb", "empiar")

ZIP_STORE_DATA_ZIP_NAME = "data.zip"

# TODO: update VolumeServerDB to store the data directly??
ANNOTATION_METADATA_FILENAME = "annotations.json"
GRID_METADATA_FILENAME = "metadata.json"
GEOMETRIC_SEGMENTATION_FILENAME = "geometric_segmentation.json"

MIN_GRID_SIZE = 100**3
DOWNSAMPLING_KERNEL = (1, 4, 6, 4, 1)

MESH_SIMPLIFICATION_CURVE_LINEAR = {
    i + 1: (10 - i) / 10 for i in range(10)
}  # {1: 1.0, 2: 0.9, 3: 0.8, 4: 0.7, 5: 0.6, 6: 0.5, 7: 0.4, 8: 0.3, 9: 0.2, 10: 0.1}
MESH_SIMPLIFICATION_N_LEVELS = 10
MESH_SIMPLIFICATION_LEVELS_PER_ORDER = 4
MESH_VERTEX_DENSITY_THRESHOLD = {
    "area": 0,  # 0 = unlimited
    # 'area': 0.02,
    # 'volume': 0.0015,
}

MIN_SIZE_PER_DOWNSAMPLING_LEVEL_MB = 5.0

NON_QUANTIZED_DATA_TYPES_STR = {
    "u2", "|u2", ">u2", "<u2"
}

METADATA_DICT_NAME = "metadata_dict"

ANNOTATIONS_DICT_NAME = "annotations_dict"

MESH_ZATTRS_NAME = "mesh_zattrs"

DEFAULT_ORIGIN = [
    0.0,
    0.0,
    0.0
]

DEFAULT_AXIS_ORDER_5D = {
    AxisName.x,
    AxisName.y,
    AxisName.z,
    AxisName.c,
    AxisName.t
}

DEFAULT_ORIGINAL_AXIS_ORDER_3D = [
    AxisName.x,
    AxisName.y,
    AxisName.z,
]
DEFAULT_SOURCE_AXES_UNITS = {
    AxisName.x: SpatialAxisUnit.angstrom,
    AxisName.y: SpatialAxisUnit.angstrom,
    AxisName.z: SpatialAxisUnit.angstrom,
}


BLANK_ENTRY_ID = EntryId(source_db_name="", source_db_id="")


TIME_INFO_STANDARD = TimeInfo(
    end=0,
    kind="range",
    start=0,
    units="millisecond",
)

INIT_ANNOTATIONS_MODEL = AnnotationsMetadata(
    descriptions={},
    details=None,
    entry_id=BLANK_ENTRY_ID,
    name=None,
    segment_annotations=[],
    volume_channels_annotations=[],
)

BLANK_SAMPLING_INFO = SamplingInfo(
    spatial_downsampling_levels=[],
    boxes={},
    time_transformations=[],
    source_axes_units={},
    original_axis_order=[],
)

INIT_METADATA_MODEL = Metadata(
    entry_id=BLANK_ENTRY_ID,
    volumes=VolumesMetadata(
        channel_ids=[],
        time_info=TIME_INFO_STANDARD,
        sampling_info=VolumeSamplingInfo(
            spatial_downsampling_levels=[],
            boxes={},
            time_transformations=[],
            source_axes_units={},
            original_axis_order=[],
            descriptive_statistics={},
        ),
    ),
    geometric_segmentation=GeometricSegmentationsMetadata(ids=[], time_info_mapping={}),
    segmentation_lattices=SegmentationLatticesMetadata(
        ids=[], sampling_info={}, time_info_mapping={}
    ),
    segmentation_meshes=MeshSegmentationsMetadata(
        ids=[], metadata={}, time_info_mapping={}
    ),
    extra_metadata=None,
)

DEFAULT_CHANNEL_IDS_MAPPING: dict[str, str] = {
    "0": "0"
}

DEFAULT_CHANNEL_ID = "0"

DEFAULT_TIME_UNITS = "millisecond"
GEOMETRIC_SEGMENTATIONS_ZATTRS = "geometric_segmentations"
RAW_GEOMETRIC_SEGMENTATION_INPUT_ZATTRS = "raw_geometric_segmentation_input"
SHORT_UNIT_NAMES_TO_LONG = {
    "µm": "micrometer",
    # TODO: support other units
}
