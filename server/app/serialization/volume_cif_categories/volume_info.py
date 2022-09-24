from db.interface.i_preprocessed_medatada import IPreprocessedMetadata
from app.api.requests import GridSliceBox

class VolumeInfo:
    def __init__(
        self,
        name: str,
        metadata: IPreprocessedMetadata,
        box: GridSliceBox,
    ):
        self.name = name
        self.metadata = metadata
        self.box = box
        
        self.grid_size = box.dimensions

        downsampling_rate = box.downsampling_rate
        voxel_size = metadata.voxel_size(downsampling_rate)
        full_grid_size = metadata.sampled_grid_dimensions(downsampling_rate)

        cartn_origin = metadata.origin()

        self.cell_size = [voxel_size[i] * full_grid_size[i] for i in range(3)]
        self.origin = [cartn_origin[i] / self.cell_size[i] for i in range(3)]
        self.dimensions = [self.grid_size[i] * voxel_size[i] / self.cell_size[i] for i in range(3)]
