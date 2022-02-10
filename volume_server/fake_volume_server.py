import json

from .preprocessed_db.i_preprocessed_db import IReadOnlyPreprocessedDb
from .i_volume_server import IVolumeServer
from .preprocessed_volume_to_cif.i_volume_to_cif_converter import IVolumeToCifConverter
from volume_server.requests.volume_request.i_volume_request import IVolumeRequest


class FakeVolumeServer(IVolumeServer):
    def __init__(self, db: IReadOnlyPreprocessedDb, volume_to_cif: IVolumeToCifConverter):
        self.db = db
        self.volume_to_cif = volume_to_cif
        self.db_namespace = "fake_db_namespace"

    async def get_volume(self, volume_request: IVolumeRequest) -> object:  # TODO: add binary cif to the project
        key = self.__volume_request_to_key__(volume_request)
        preprocessed_volume = await self.db.read(self.db_namespace, key)
        # TODO: do something with preprocessed?
        cif = self.volume_to_cif.convert(preprocessed_volume)
        # TODO: do something with cif?
        return cif

    @staticmethod
    def __volume_request_to_key__(volume_request: IVolumeRequest) -> str:
        return json.dumps(volume_request.__dict__)
