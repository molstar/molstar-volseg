import numpy as np
from typing import Dict, List, TypedDict, Optional, Protocol

class MeshMetadata(TypedDict):
    num_vertices: int
    num_triangles: int
    num_normals: int

class MeshListMetadata(TypedDict):
    mesh_ids: dict[int, MeshMetadata]

class DetailLvlsMetadata(TypedDict):
    detail_lvls: dict[int, MeshListMetadata]

class MeshComponentNumbers(TypedDict):
    segment_ids: dict[int, DetailLvlsMetadata]

class SegmentationSliceData(TypedDict):
    # array with set ids
    category_set_ids: np.ndarray
    # dict mapping set ids to the actual segment ids (e.g. for set id=1, there may be several segment ids)
    category_set_dict: Dict

class VolumeSliceData(TypedDict):
    # changed segm slice to another typeddict
    segmentation_slice: Optional[SegmentationSliceData]
    volume_slice: Optional[np.ndarray]


class VolumeMetadata(Protocol):
    def json_metadata(self) -> str:
        ...

    
    def segmentation_lattice_ids(self) -> List[int]:
        ...

    
    def segmentation_downsamplings(self, lattice_id: int) -> List[int]:
        ...

    
    def volume_downsamplings(self) -> List[int]:
        ...

    
    def origin(self) -> List[float]:
        '''
        Returns the coordinates of the initial point in Angstroms
        '''
        ...
    
    
    def voxel_size(self, downsampling_rate: int) -> List[float]:
        '''
        Returns the step size in Angstroms for each axis (X, Y, Z) for a given downsampling rate
        '''
        ...

    
    def grid_dimensions(self)  -> List[int]:
        '''
        Returns the number of points along each axis (X, Y, Z)
        '''
        ...
    
    
    def sampled_grid_dimensions(self, level: int) -> List[int]:
        '''
        Returns the number of points along each axis (X, Y, Z) for specific downsampling level
        '''
        ...

    
    def mean(self, level: int)  -> np.float32:
        '''
        Return mean for data at given downsampling level
        '''
        ...

    
    def std(self, level: int)  -> np.float32:
        '''
        Return standard deviation for data at given downsampling level
        '''
        ...
    
    
    def max(self, level: int)  -> np.float32:
        '''
        Return max for data at given downsampling level
        '''
        ...
    
    
    def min(self, level: int)  -> np.float32:
        '''
        Return min for data at given downsampling level
        '''
        ...

    
    def mesh_component_numbers(self) -> MeshComponentNumbers:
        '''
        Return typed dict with numbers of mesh components (triangles, vertices etc.) for
        each segment, detail level and mesh id
        '''
        ...

    
    def detail_lvl_to_fraction(self) -> dict:
        '''
        Returns dict with detail lvls (1,2,3 ...) as keys and corresponding
        mesh simplification ratios (fractions, e.g. 0.8) as values
        '''
        ...