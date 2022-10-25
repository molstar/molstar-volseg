from db.models import VolumeMetadata

from app.core.models import GridSliceBox


class VolumeInfo:
    def __init__(
        self,
        name: str,
        metadata: VolumeMetadata,
        box: GridSliceBox,
        axis_order: tuple[int, int, int] = (0, 1, 2)
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
        self.origin = [(cartn_origin[i] + box.bottom_left[i] * voxel_size[i]) / self.cell_size[i] for i in range(3)]
        self.dimensions = [self.grid_size[i] * voxel_size[i] / self.cell_size[i] for i in range(3)]

        self.axis_order = axis_order
