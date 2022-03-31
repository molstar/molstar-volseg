import abc
from typing import List, TypedDict

# TODO: when retriving annotations, remember that in dict value = 0 is assigned segm id = 0, but
# there is no such segment in annotation. Leave it like this or switch to None.
# it simply should be taken into account when retriving annotations for a segment id
# e.g. if segm_id == 0 => return None or don't allow to put < 1 as argument to method retrieving annotation
class AnnotationAndMetadata(TypedDict):
    pass
    # TODO: define a structure

# TODO: define sequentially inner TypedDicts


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
    
    @abc.abstractmethod
    def annotations_and_metadata(self) -> AnnotationAndMetadata:
        '''
        Returns all annotations/metadata as a typedDict
        '''
        pass