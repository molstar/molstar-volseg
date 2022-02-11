import abc

from volume_server.requests.volume_request.i_volume_request import IVolumeRequest


class IVolumeServer(abc.ABC):
    @abc.abstractmethod
    async def get_volume(self, volume_request: IVolumeRequest) -> object:  # TODO: add binary cif to the project
        pass
