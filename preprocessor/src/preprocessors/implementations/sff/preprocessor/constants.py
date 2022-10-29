from pathlib import Path


MESH_SIMPLIFICATION_CURVE_LINEAR = {i + 1: (10-i)/10 for i in range(10)}  # {1: 1.0, 2: 0.9, 3: 0.8, 4: 0.7, 5: 0.6, 6: 0.5, 7: 0.4, 8: 0.3, 9: 0.2, 10: 0.1}
MESH_SIMPLIFICATION_N_LEVELS = 10
MESH_SIMPLIFICATION_LEVELS_PER_ORDER = 4
MESH_VERTEX_DENSITY_THRESHOLD = {
    'area': 0,  # 0 = unlimited
    # 'area': 0.02,
    # 'volume': 0.0015,
}
# temporarly can be set to 32 to check at least x4 downsampling with 64**3 emd-1832 grid
MIN_GRID_SIZE = 100**3
DOWNSAMPLING_KERNEL = (1, 4, 6, 4, 1)
# TODO: change to big EMDB entry name once ready
OUTPUT_FILEPATH = Path('test-data/preprocessor/fake_segmentations/fake_emd_1832.hff')
# Just for testing
# FILEPATH_JSON = Path('preprocessor/fake_segmentations/fake_emd_1832.json')

REAL_MAP_FILEPATH = Path('test-data/preprocessor/sample_volumes/emdb_sff/EMD-1832.map')

# NOTE: inside this folder, there will be subfolder with name = last path component of db_path
TEMP_ZARR_HIERARCHY_STORAGE_PATH = Path('test-data/preprocessor/temp_zarr_hierarchy_storage')

PARAMETRIZED_DBS_INPUT_PARAMS_FILEPATH = Path('parametrized_dbs_input_params.txt')

RAW_INPUT_FILES_DIR = Path('test-data/preprocessor//raw_input_files')
DEFAULT_DB_PATH = Path('test-data/db') 
DEFAULT_QUANTIZE_DTYPE_STR = 'u1'
APPLICATION_SPECIFIC_SEGMENTATION_EXTENSIONS = ['.am', '.mod', '.seg', '.surf', '.stl']
CSV_WITH_ENTRY_IDS_FILE = Path('test-data/preprocessor//entry_ids.csv')

MAP_SIZE_THRESHOLD_FOR_DASK_METHODS = 2 * 10**9
# MAP_SIZE_THRESHOLD_FOR_DASK_METHODS = 1