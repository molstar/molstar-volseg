import abc
from typing import List


class IPreprocessedMetadata(abc.ABC):
    @abc.abstractmethod
    def segmentation_lattice_ids(self) -> List[int]:
        pass

    @abc.abstractmethod
    def segmentation_downsamplings(self, lattice_id: int) -> List[int]:
        pass

    @abc.abstractmethod
    def volume_downsamplings(self) -> List[int]:
        pass

    @abc.abstractmethod
    def origin(self) -> List[float]:
        '''
        Returns the coordinates of the initial point in Angstroms
        '''
        pass
    
    @abc.abstractmethod
    def voxel_size(self, downsampling_rate: int) -> List[float]:
        '''
        Returns the step size in Angstroms for each axis (X, Y, Z) for a given downsampling rate
        '''
        pass

    @abc.abstractmethod
    def grid_dimensions(self)  -> List[int]:
        '''
        Returns the number of points along each axis (X, Y, Z)
        '''
        pass    
