from db.interface.i_preprocessed_medatada import IPreprocessedMetadata


class VolumeInfo:
    def __init__(self,
                 name: str,
                 metadata: IPreprocessedMetadata,
                 downsampling: int,
                 min_downsampled: float,
                 max_downsampled: float,
                 min_source: float,
                 max_source: float,
                 grid_size: list[int]):
        self.name = name
        self.metadata = metadata
        self.downsampling = downsampling
        self.min_downsampled = min_downsampled
        self.max_downsampled = max_downsampled
        self.min_source = min_source
        self.max_source = max_source
        self.grid_size = grid_size


        # NOTE: this isn't accurate, but should be good enough for the prototype
        nx, ny, nz = metadata.grid_dimensions()
        self.downsampled_grid_size = [int(nx / downsampling), int(ny / downsampling), int(nz / downsampling)]
        vx, vy, vz = metadata.voxel_size(1)
        dx, dy, dz = self.downsampled_grid_size

        self.dimensions = [grid_size[0] / dx, grid_size[1] / dy, grid_size[2] / dz]
        self.cell_size = [vx * nx, vy * ny, vz * nz]

        # hack for emd 99999 demo
        if downsampling == 8:
            self.cell_size[2] *= 3
