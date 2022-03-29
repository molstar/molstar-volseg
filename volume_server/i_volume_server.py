import abc

from db.interface.i_preprocessed_medatada import IPreprocessedMetadata
from volume_server.requests.metadata_request.i_metadata_request import IMetadataRequest
from volume_server.requests.volume_request.i_volume_request import IVolumeRequest


class IVolumeServer(abc.ABC):
    @abc.abstractmethod
    async def get_volume(self, req: IVolumeRequest) -> object:  # TODO: add binary cif to the project
        pass

    @abc.abstractmethod
    async def get_metadata(self, req: IMetadataRequest) -> IPreprocessedMetadata:
        pass
