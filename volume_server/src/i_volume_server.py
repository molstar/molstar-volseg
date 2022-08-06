import abc

from volume_server.src.requests.cell_request.i_cell_request import ICellRequest
from volume_server.src.requests.metadata_request.i_metadata_request import IMetadataRequest
from volume_server.src.requests.volume_request.i_volume_request import IVolumeRequest


class IVolumeServer(abc.ABC):
    @abc.abstractmethod
    async def get_volume(self, req: IVolumeRequest) -> tuple:  # TODO: add binary cif to the project
        pass

    @abc.abstractmethod
    async def get_cell(self, req: ICellRequest) -> bytes:
        pass

    @abc.abstractmethod
    async def get_metadata(self, req: IMetadataRequest) -> str:
        pass
