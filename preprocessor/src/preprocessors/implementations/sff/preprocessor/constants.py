from pathlib import Path

MESH_SIMPLIFICATION_CURVE = sorted([(detail_lvl, ratio/10) for detail_lvl, ratio in enumerate(range(9, 0, -1), 2)])
# [(2, 0.9), (3, 0.8), (4, 0.7), (5, 0.6), (6, 0.5), (7, 0.4), (8, 0.3), (9, 0.2), (10, 0.1)]
MESH_VERTEX_DENSITY_THRESHOLD = {
    'area': 0.02,
    # 'volume': 0.0015,
}
VOLUME_DATA_GROUPNAME = '_volume_data'
SEGMENTATION_DATA_GROUPNAME = '_segmentation_data'
GRID_METADATA_FILENAME = 'metadata.json'
ANNOTATION_METADATA_FILENAME = 'annotations.json'
# temporarly can be set to 32 to check at least x4 downsampling with 64**3 emd-1832 grid
MIN_GRID_SIZE = 100**3
DOWNSAMPLING_KERNEL = (1, 4, 6, 4, 1)
# TODO: change to big EMDB entry name once ready
OUTPUT_FILEPATH = Path('preprocessor/data/fake_segmentations/fake_emd_1832.hff')
# Just for testing
# FILEPATH_JSON = Path('preprocessor/fake_segmentations/fake_emd_1832.json')

REAL_MAP_FILEPATH = Path('preprocessor/data/sample_volumes/emdb_sff/EMD-1832.map')

TEMP_ZARR_HIERARCHY_STORAGE_PATH = Path('preprocessor/data/temp_zarr_hierarchy_storage')

DB_NAMESPACES = ('emdb', 'empiar')