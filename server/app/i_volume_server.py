import abc
from typing import Optional

from app.requests.entries_request.i_entries_request import IEntriesRequest
from app.requests.mesh_request.i_mesh_request import IMeshRequest
from app.requests.metadata_request.i_metadata_request import IMetadataRequest

from app.requests.volume import VolumeRequestInfo, VolumeRequestBox


class IVolumeServer(abc.ABC):
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
