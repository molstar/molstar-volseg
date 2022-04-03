from math import ceil

from db.interface.i_preprocessed_db import IReadOnlyPreprocessedDb
from db.interface.i_preprocessed_medatada import IPreprocessedMetadata
from .i_volume_server import IVolumeServer
from .preprocessed_volume_to_cif.i_volume_to_cif_converter import IVolumeToCifConverter
from volume_server.requests.volume_request.i_volume_request import IVolumeRequest
from .requests.metadata_request.i_metadata_request import IMetadataRequest


class VolumeServerV1(IVolumeServer):
    async def get_metadata(self, req: IMetadataRequest) -> IPreprocessedMetadata:
        return await self.db.read_grid_metadata(req.source(), req.structure_id())

    def __init__(self, db: IReadOnlyPreprocessedDb, volume_to_cif: IVolumeToCifConverter):
        self.db = db
        self.volume_to_cif = volume_to_cif

    async def get_volume(self, req: IVolumeRequest) -> object:  # TODO: add binary cif to the project
        metadata = await self.db.read_grid_metadata(req.source(), req.structure_id())
        lattice = self.decide_lattice(req, metadata)
        grid = self.decide_grid(req, metadata)
        print("Converted grid to: " + str(grid))

        down_sampling = self.decide_down_sampling(grid, req, metadata)
        print("Decided down_sampling to be: " + str(down_sampling))

        grid = self.down_sampled_grid(down_sampling, grid)

        print("Converted grid (down sampled) to: " + str(grid))
        db_slice = await self.db.read_slice(
            req.source(),
            req.structure_id(),
            lattice,
            down_sampling,
            grid,
            mode="zarr_colon")

        volume = db_slice["volume_slice"]
        # TODO: do something with preprocessed?
        cif = self.volume_to_cif.convert(volume)
        # TODO: do something with cif?
        return cif

    def decide_lattice(self, req: IVolumeRequest, metadata: IPreprocessedMetadata) -> int:
        if req.segmentation_id() not in metadata.segmentation_lattice_ids():
            return metadata.segmentation_lattice_ids()[0]
        return req.segmentation_id()

    def decide_down_sampling(self, original_grid: tuple[tuple[int,int,int], tuple[int,int,int]],
                             req: IVolumeRequest, metadata: IPreprocessedMetadata) -> int:

        # TODO: it seems that downsamplings are strings -> check and fix

        down_samplings = metadata.volume_downsamplings()
        if not req.max_points():
            return 1 if '1' in down_samplings else int(down_samplings[0])

        grid_x = original_grid[1][0] - original_grid[0][0]
        grid_y = original_grid[1][1] - original_grid[0][1]
        grid_z = original_grid[1][2] - original_grid[0][2]

        grid_size = grid_x * grid_y * grid_z
        # TODO: improve rounding depending on conservative, strict, etc approach
        desired_down_sampling = ceil(grid_size/req.max_points())

        for ds in down_samplings:
            if int(ds) >= desired_down_sampling:
                return int(ds)

        return int(down_samplings[-1])  # TODO: check assumption that last is highest


    def decide_grid(self, req: IVolumeRequest, meta: IPreprocessedMetadata) \
            -> tuple[tuple[int,int,int], tuple[int,int,int]]:
        return (
            (self._float_to_grid(meta.origin()[0], meta.voxel_size(1)[0], meta.grid_dimensions()[0], req.x_min()),
             self._float_to_grid(meta.origin()[1], meta.voxel_size(1)[1], meta.grid_dimensions()[1], req.y_min()),
             self._float_to_grid(meta.origin()[2], meta.voxel_size(1)[2], meta.grid_dimensions()[2], req.z_min())),
            (self._float_to_grid(meta.origin()[0], meta.voxel_size(1)[0], meta.grid_dimensions()[0], req.x_max()),
             self._float_to_grid(meta.origin()[1], meta.voxel_size(1)[1], meta.grid_dimensions()[1], req.y_max()),
             self._float_to_grid(meta.origin()[2], meta.voxel_size(1)[2], meta.grid_dimensions()[2], req.z_max())))

    def down_sampled_grid(self, down_sampling: int, original_grid: tuple[tuple[int, int, int], tuple[int, int, int]]) \
            -> list[list]:

        result: list[list] = []

        if down_sampling > 1:
            for i in range(2):
                result.append([])
                for j in range(3):
                    result[i].append(round(original_grid[i][j]/2))

        return result

    def _float_to_grid(self, origin: float, step: float, grid_size: int, to_convert: float) -> int:
        if to_convert < origin:
            return 0

        if to_convert > origin + step * (grid_size - 1):
            return grid_size

        return round((to_convert - origin)/step)
