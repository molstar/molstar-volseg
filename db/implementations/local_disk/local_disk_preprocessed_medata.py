from typing import List, Dict
from db.interface.i_preprocessed_medatada import IPreprocessedMetadata

class LocalDiskPreprocessedMetadata(IPreprocessedMetadata):
    def __init__(self, raw_metadata: Dict):
        self.raw_metadata = raw_metadata

    def segmentation_lattice_ids(self) -> List[int]:
        return self.raw_metadata['segmentation_lattice_ids']

    def segmentation_downsamplings(self, lattice_id: int) -> List[int]:
        return self.raw_metadata['segmentation_downsamplings'][str(lattice_id)]

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


