import json

from db.interface.i_preprocessed_db import IReadOnlyPreprocessedDb
from db.interface.i_preprocessed_medatada import IPreprocessedMetadata
from .i_volume_server import IVolumeServer
from .preprocessed_volume_to_cif.i_volume_to_cif_converter import IVolumeToCifConverter
from volume_server.requests.volume_request.i_volume_request import IVolumeRequest


class VolumeServerV1(IVolumeServer):
    def __init__(self, db: IReadOnlyPreprocessedDb, volume_to_cif: IVolumeToCifConverter):
        self.db = db
        self.volume_to_cif = volume_to_cif

    async def get_volume(self, vr: IVolumeRequest) -> object:  # TODO: add binary cif to the project
        metadata = await self.db.read_metadata(vr.source(), vr.structure_id())
        lattice = self.decide_lattice(metadata)
        down_sampling = self.decide_down_sampling(metadata)
        grid = self.decide_grid(down_sampling, metadata, vr)
        db_slice = await self.db.read_slice(
            vr.source(),
            vr.structure_id(),
            lattice,
            down_sampling,
            grid,
            mode="zarr_colon")

        volume = db_slice["volume_slice"]
        # TODO: do something with preprocessed?
        cif = self.volume_to_cif.convert(volume)
        # TODO: do something with cif?
        return cif

    def decide_lattice(self, metadata: IPreprocessedMetadata) -> int:
        return 0

    def decide_down_sampling(self, metadata: IPreprocessedMetadata) -> int:
        return 2

    def decide_grid(self, downsampling: int, metadata: IPreprocessedMetadata, vr: IVolumeRequest) \
            -> tuple[tuple[int,int,int], tuple[int,int,int]]:
        return ((0, 0, 0), (10, 10, 10))
