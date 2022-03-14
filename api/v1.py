from typing import Optional

from fastapi import FastAPI
from volume_server.i_volume_server import IVolumeServer
from volume_server.requests.volume_request.volume_request import VolumeRequest


def configure_endpoints(app: FastAPI, volume_server: IVolumeServer):
    @app.get("/{source}/{id}/box/{a1}/{a2}/{a3}/{b1}/{b2}/{b3}/{max_size_kb}")
    async def get_volume(
            source: str,
            id: str,
            a1: float,
            a2: float,
            a3: float,
            b1: float,
            b2: float,
            b3: float,
            max_size_kb: Optional[int] = 0
    ):
        volume_request = VolumeRequest(source, id, a1, a2, a3, b1, b2, b3, max_size_kb)
        requested_slice = await volume_server.get_volume(volume_request)

        # TODO: serialize
        serialized = str(requested_slice.dumps())
        return serialized
