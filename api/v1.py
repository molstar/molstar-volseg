from typing import Optional

from fastapi import FastAPI, Response

from volume_server.i_volume_server import IVolumeServer
from volume_server.requests.metadata_request.metadata_request import MetadataRequest
from volume_server.requests.volume_request.volume_request import VolumeRequest


def configure_endpoints(app: FastAPI, volume_server: IVolumeServer):
    @app.get("/v1/{source}/{id}/box/{segmentation}/{a1}/{a2}/{a3}/{b1}/{b2}/{b3}/{max_points}")
    async def get_volume(
            source: str,
            id: str,
            segmentation: int,
            a1: float,
            a2: float,
            a3: float,
            b1: float,
            b2: float,
            b3: float,
            max_points: Optional[int] = 0
    ):
        request = VolumeRequest(source, id, segmentation, a1, a2, a3, b1, b2, b3, max_points)
        response = await volume_server.get_volume(request)

        return Response(response)

    @app.get("/v1/{source}/{id}/metadata")
    async def get_metadata(
            source: str,
            id: str,
    ):
        request = MetadataRequest(source, id)
        metadata = await volume_server.get_metadata(request)

        return Response(metadata)
