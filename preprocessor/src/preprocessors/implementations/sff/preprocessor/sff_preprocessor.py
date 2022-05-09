import base64
import json
import gemmi
from pathlib import Path
from typing import Dict, Set, Tuple, List
import zlib
import zarr
import numcodecs
import h5py
import numpy as np
import decimal
from decimal import Decimal
from preprocessor.src.preprocessors.i_data_preprocessor import IDataPreprocessor
import math
from sfftkrw import SFFSegmentation
from scipy import signal

VOLUME_DATA_GROUPNAME = '_volume_data'
SEGMENTATION_DATA_GROUPNAME = '_segmentation_data'
GRID_METADATA_FILENAME = 'grid_metadata.json'
ANNOTATION_METADATA_FILENAME = 'annotation_metadata.json'
# temporarly can be set to 32 to check at least x4 downsampling with 64**3 emd-1832 grid
MIN_GRID_SIZE = 100**3
DOWNSAMPLING_KERNEL = (1, 4, 6, 4, 1)


'''
class Bigclass(object):

    from classdef1 import foo, bar, baz, quux
    from classdef2 import thing1, thing2
    from classdef3 import magic, moremagic
    # unfortunately, "from classdefn import *" is an error or warning
'''


def open_zarr_structure_from_path(path: Path) -> zarr.hierarchy.Group:
    store: zarr.storage.DirectoryStore = zarr.DirectoryStore(str(path))
    # Re-create zarr hierarchy from opened store
    root: zarr.hierarchy.group = zarr.group(store=store)
    return root


class SFFPreprocessor(IDataPreprocessor):
    # TODO: import from e.g. axis methods etc.

    def __init__(self):
        # path to root of temporary storage for zarr hierarchy
        self.temp_root_path = Path(__file__).parents[1] / 'temp_zarr_hierarchy_storage'
        # path to temp storage for that entry (segmentation)
        self.temp_zarr_structure_path = None

    def preprocess(self, segm_file_path: Path, volume_file_path: Path, volume_force_dtype=np.float32):
        '''
        Returns path to temporary zarr structure that will be stored permanently using db.store
        '''
        if segm_file_path != None:
            self.__hdf5_to_zarr(segm_file_path)
        else:
            self.__initialize_empty_zarr_structure(volume_file_path)
        # Re-create zarr hierarchy
        zarr_structure: zarr.hierarchy.group = open_zarr_structure_from_path(
            self.temp_zarr_structure_path)
        
        # read map
        map_object = self.__read_volume_map_to_object(volume_file_path)
        normalized_axis_map_object = self.__normalize_axis_order(map_object)
        
        if segm_file_path != None:
            self.__process_segmentation_data(zarr_structure)
        
        self.__process_volume_data(zarr_structure, normalized_axis_map_object, volume_force_dtype)
        
        grid_metadata = self.__extract_grid_metadata(zarr_structure, normalized_axis_map_object)
        self.__temp_save_metadata(grid_metadata, GRID_METADATA_FILENAME, self.temp_zarr_structure_path)

        if segm_file_path != None:
            annotation_metadata = self.__extract_annotation_metadata(segm_file_path)
            self.__temp_save_metadata(annotation_metadata, ANNOTATION_METADATA_FILENAME, self.temp_zarr_structure_path)

        return self.temp_zarr_structure_path


    
    
    
    
    def __initialize_empty_zarr_structure(self, volume_file_path: Path):
        '''
        Creates EMPTY temp zarr structure for the case when just volume file is provided
        '''
        self.temp_zarr_structure_path = self.temp_root_path / volume_file_path.stem
        store: zarr.storage.DirectoryStore = zarr.DirectoryStore(str(self.temp_zarr_structure_path))

    
    

