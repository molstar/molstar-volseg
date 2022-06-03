from pathlib import Path

VOLUME_DATA_GROUPNAME = '_volume_data'
SEGMENTATION_DATA_GROUPNAME = '_segmentation_data'
GRID_METADATA_FILENAME = 'grid_metadata.json'
ANNOTATION_METADATA_FILENAME = 'annotations.json'
# temporarly can be set to 32 to check at least x4 downsampling with 64**3 emd-1832 grid
MIN_GRID_SIZE = 100**3
DOWNSAMPLING_KERNEL = (1, 4, 6, 4, 1)
# TODO: change to big EMDB entry name once ready
OUTPUT_FILEPATH = Path('preprocessor/data/fake_segmentations/fake_emd_1832.hff')
# Just for testing
# FILEPATH_JSON = Path('preprocessor/fake_segmentations/fake_emd_1832.json')

REAL_MAP_FILEPATH = Path('preprocessor/data/sample_volumes/emdb_sff/EMD-1832.map')