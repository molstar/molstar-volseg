import logging
from typing import List, Dict

import numpy as np
from db.interface.i_preprocessed_medatada import IPreprocessedMetadata
from preprocessor.src.preprocessors.implementations.sff.preprocessor._metadata_methods import MeshComponentNumbers


class LocalDiskPreprocessedMetadata(IPreprocessedMetadata):
    def __init__(self, raw_metadata: Dict):
        print("Metadata " + str(raw_metadata))
        self.raw_metadata = raw_metadata

    def json_metadata(self) -> str:
        return self.raw_metadata

    def segmentation_lattice_ids(self) -> List[int]:
        return self.raw_metadata['segmentation_lattices']['segmentation_lattice_ids']

    def segmentation_downsamplings(self, lattice_id: int) -> List[int]:
        s = []
        try:
            s = self.raw_metadata['segmentation_lattices']['segmentation_downsamplings'][str(lattice_id)]
        except Exception as e:
            logging.error(e, stack_info=True, exc_info=True)
        return s
            

    def volume_downsamplings(self) -> List[int]:
        return self.raw_metadata['volumes']['volume_downsamplings']

    def origin(self) -> List[float]:
        '''
        Returns coordinates of initial point in Angstroms (X, Y, Z)
        '''
        # origin_str = self.raw_metadata['origin']
        # origin_float = List([float(i) for i in origin_str])
        return self.raw_metadata['volumes']['origin']
        
    def voxel_size(self, downsampling_rate: int) -> List[float]:
        '''
        Returns the step size in Angstroms for each axis (X, Y, Z) for a given downsampling rate
        '''
        # voxel_sizes_dict = self.raw_metadata['voxel_size']

        # voxel_float = List([float(i) for i in voxel_str])
        # return voxel_float
        return self.raw_metadata['volumes']['voxel_size'][str(downsampling_rate)]

    def grid_dimensions(self)  -> List[int]:
        '''
        Returns the number of points along each axis (X, Y, Z)
        '''
        return self.raw_metadata['volumes']['grid_dimensions']

    def sampled_grid_dimensions(self, level: int) -> List[int]:
        '''
        Returns the number of points along each axis (X, Y, Z) for specific downsampling level
        '''
        return self.raw_metadata['volumes']['sampled_grid_dimensions'][str(level)]

    def mean(self, level: int)  -> np.float64:
        '''Return mean for data at given downsampling level'''
        return np.float32(self.raw_metadata['volumes']['mean'][str(level)])

    def std(self, level: int)  -> np.float64:
        '''Return standard deviation for data at given downsampling level'''
        return np.float32(self.raw_metadata['volumes']['std'][str(level)])

    def max(self, level: int)  -> np.float64:
        '''Return max for data at given downsampling level'''
        return np.float32(self.raw_metadata['volumes']['max'][str(level)])
    
    def min(self, level: int)  -> np.float64:
        '''Return min for data at given downsampling level'''
        return np.float32(self.raw_metadata['volumes']['min'][str(level)])

    def mesh_component_numbers(self) -> MeshComponentNumbers:
        '''Return typed dict with numbers of mesh components (triangles, vertices etc.) for
        each segment, detail level and mesh id'''
        return self.raw_metadata['segmentation_meshes']['mesh_component_numbers']

    def detail_lvl_to_fraction(self) -> dict:
        '''Returns dict with detail lvls (1,2,3 ...) as keys and corresponding
        mesh simplification ratios (fractions, e.g. 0.8) as values'''
        return self.raw_metadata['segmentation_meshes']['detail_lvl_to_fraction']
