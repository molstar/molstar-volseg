import numpy
from fastapi import FastAPI
from volume_server.i_volume_server import IVolumeServer
from volume_server.requests.volume_request.volume_request import VolumeRequest


def configure_endpoints(app: FastAPI, volume_server: IVolumeServer):
    @app.get("/{source}/{structure_id}/")
    async def get_volume(
            source: str,
            structure_id: str,
            x_min: int = -1,
            y_min: int = -1,
            z_min: int = -1,
            x_max: int = -1,
            y_max: int = -1,
            z_max: int = -1
    ):
        volume_request = VolumeRequest(source, structure_id, x_min, y_min, z_min, x_max, y_max, z_max)
        volume_result = await volume_server.get_volume(volume_request)

        # TODO: serialize
        return str(numpy.ndarray(volume_result).dumps())
