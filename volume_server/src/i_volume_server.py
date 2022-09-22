import abc
from typing import Optional

from volume_server.src.requests.cell_request.i_cell_request import ICellRequest
from volume_server.src.requests.entries_request.i_entries_request import IEntriesRequest
from volume_server.src.requests.mesh_request.i_mesh_request import IMeshRequest
from volume_server.src.requests.metadata_request.i_metadata_request import IMetadataRequest
from volume_server.src.requests.volume_request.i_volume_request import IVolumeRequest

from volume_server.src.requests.volume import VolumeRequestInfo, VolumeRequestBox


class IVolumeServer(abc.ABC):
    @abc.abstractmethod
    async def get_volume(self, req: IVolumeRequest) -> tuple:  # TODO: add binary cif to the project
        pass

    @abc.abstractmethod
    async def get_cell(self, req: ICellRequest) -> bytes:
        pass

    @abc.abstractmethod
    async def get_volume_data(self, req: VolumeRequestInfo, req_box: Optional[VolumeRequestBox] = None) -> bytes:
        pass

    @abc.abstractmethod
    async def get_metadata(self, req: IMetadataRequest) -> str:
        pass

    @abc.abstractmethod
    async def get_meshes(self, req: IMeshRequest) -> list[object]:
        pass

    @abc.abstractmethod
    async def get_entries(self, req: IEntriesRequest) -> dict:
        pass
