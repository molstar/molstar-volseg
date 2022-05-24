import logging
from typing import List, Dict

import numpy as np
from db.interface.i_preprocessed_medatada import IPreprocessedMetadata


class LocalDiskPreprocessedMetadata(IPreprocessedMetadata):
    def __init__(self, raw_metadata: Dict):
        print("Metadata " + str(raw_metadata))
        self.raw_metadata = raw_metadata

    def json_metadata(self) -> str:
        return self.raw_metadata

    def segmentation_lattice_ids(self) -> List[int]:
        return self.raw_metadata['segmentation_lattice_ids']

    def segmentation_downsamplings(self, lattice_id: int) -> List[int]:
        s = []
        try:
            s = self.raw_metadata['segmentation_downsamplings'][str(lattice_id)]
        except Exception as e:
            logging.error(e, stack_info=True, exc_info=True)
        return s
            

    def volume_downsamplings(self) -> List[int]:
        return self.raw_metadata['volume_downsamplings']

    def origin(self) -> List[float]:
        '''
        Returns coordinates of initial point in Angstroms (X, Y, Z)
        '''
        # origin_str = self.raw_metadata['origin']
        # origin_float = List([float(i) for i in origin_str])
        return self.raw_metadata['origin']
        
    def voxel_size(self, downsampling_rate: int) -> List[float]:
        '''
        Returns the step size in Angstroms for each axis (X, Y, Z) for a given downsampling rate
        '''
        # voxel_sizes_dict = self.raw_metadata['voxel_size']

        # voxel_float = List([float(i) for i in voxel_str])
        # return voxel_float
        return self.raw_metadata['voxel_size'][str(downsampling_rate)]

    def grid_dimensions(self)  -> List[int]:
        '''
        Returns the number of points along each axis (X, Y, Z)
        '''
        return self.raw_metadata['grid_dimensions']

    def sampled_grid_dimensions(self, level: int) -> List[int]:
        '''
        Returns the number of points along each axis (X, Y, Z) for specific downsampling level
        '''
        return self.raw_metadata['sampled_grid_dimensions'][str(level)]

    def mean(self, level: int)  -> np.float64:
        '''Return mean for data at given downsampling level'''
        return np.float32(self.raw_metadata['mean'][str(level)])

    def std(self, level: int)  -> np.float64:
        '''Return standard deviation for data at given downsampling level'''
        return np.float32(self.raw_metadata['std'][str(level)])

