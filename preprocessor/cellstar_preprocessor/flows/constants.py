from pathlib import Path

from cellstar_db.models import AnnotationsMetadata, Metadata

CSV_WITH_ENTRY_IDS_FILE = Path(
    "test-data/preprocessor/db_building_parameters_custom_entries.csv"
)
DEFAULT_DB_PATH = "preprocessor/temp/test_db"
RAW_INPUT_FILES_DIR = "preprocessor/temp/raw_input_files_dir"
DB_BUILDING_PARAMETERS_JSON = "test-data/preprocessor/db_building_parameters.json"
RAW_INPUT_DOWNLOAD_PARAMS_JSON = "test-data/preprocessor/download_raw_input_params.json"
TEMP_ZARR_HIERARCHY_STORAGE_PATH = "preprocessor/temp/temp_zarr_hierarchy_storage"
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

SPACE_UNITS_CONVERSION_DICT = {"micrometer": 10000, "angstrom": 1}

INIT_ANNOTATIONS_DICT: AnnotationsMetadata = {
    "descriptions": {},
    "details": None,
    "entry_id": {"source_db_name": None, "source_db_id": None},
    "name": None,
    "segment_annotations": [],
    "volume_channels_annotations": [],
}

# TODO: fill more levels if needed
INIT_METADATA_DICT: Metadata = {
    "entry_id": {"source_db_name": None, "source_db_id": None},
    "volumes": {},
    "geometric_segmentation": {"segmentation_ids": [], "time_info": {}},
    "segmentation_lattices": {
        "segmentation_ids": [],
        "segmentation_sampling_info": {},
        "time_info": {},
    },
    "segmentation_meshes": {
        "segmentation_metadata": {},
        "segmentation_ids": [],
        "time_info": {},
    },
    "extra_metadata": {},
    "entry_metadata": {}
}

GEOMETRIC_SEGMENTATIONS_ZATTRS = "geometric_segmentations"
RAW_GEOMETRIC_SEGMENTATION_INPUT_ZATTRS = "raw_geometric_segmentation_input"
SHORT_UNIT_NAMES_TO_LONG = {
    "µm": "micrometer",
    # TODO: support other units
}
