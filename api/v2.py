import json
from typing import Optional

from fastapi import FastAPI, Response
from starlette.responses import JSONResponse

from volume_server.src.i_volume_server import IVolumeServer
from volume_server.src.requests.entries_request.entries_request import EntriesRequest
from volume_server.src.requests.mesh_request.mesh_request import MeshRequest
from volume_server.src.requests.metadata_request.metadata_request import MetadataRequest
from volume_server.src.requests.volume_request.volume_request import VolumeRequest
from .json_numpy_response import JSONNumpyResponse

HTTP_CODE_UNPROCESSABLE_ENTITY = 422


def configure_endpoints(app: FastAPI, volume_server: IVolumeServer):
    @app.get("/v2/list_entries/{limit}")
    async def get_entries(
            limit: int = 100
    ):
        request = EntriesRequest(limit, "")
        response = await volume_server.get_entries(request)

        return response

    @app.get("/v2/list_entries/{limit}/{keyword}")
    async def get_entries_keyword(
            keyword: str,
            limit: int = 100
    ):
        request = EntriesRequest(limit, keyword)
        response = await volume_server.get_entries(request)

        return response

    @app.get("/v2/{source}/{id}/segmentation/box/{segmentation}/{a1}/{a2}/{a3}/{b1}/{b2}/{b3}/{max_points}")
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

        # return {}
        return Response(response, headers={"Content-Disposition": f'attachment;filename="{id}.bcif"'})

    @app.get("/v2/{source}/{id}/volume/box/{a1}/{a2}/{a3}/{b1}/{b2}/{b3}/{max_points}")
    async def get_volume(
            source: str,
            id: str,
            a1: float,
            a2: float,
            a3: float,
            b1: float,
            b2: float,
            b3: float,
            max_points: Optional[int] = 0
    ):
        # TODO: not sure if trying to get segment 0 is enough or if this code should pass None/-1 to be parsed downstream
        # TODO: check with aliaksey
        request = VolumeRequest(source, id, 0, a1, a2, a3, b1, b2, b3, max_points)
        response = await volume_server.get_volume(request)

        # return {}
        return Response(response, headers={"Content-Disposition": f'attachment;filename="{id}.bcif"'})

    @app.get("/v2/{source}/{id}/segmentation/cell/{segmentation}/{max_points}")
    async def get_cell(
            source: str,
            id: str,
            segmentation: int,
            max_points: Optional[int] = 0
    ):
        request = VolumeRequest(source, id, segmentation, -100000, -100000, -100000, 100000, 100000, 100000, max_points)
        response = await volume_server.get_volume(request)

        # return {}
        return Response(response, headers={"Content-Disposition": f'attachment;filename="{id}.bcif"'})

    @app.get("/v2/{source}/{id}/volume/cell/{max_points}")
    async def get_cell(
            source: str,
            id: str,
            max_points: Optional[int] = 0
    ):
        #TODO: not sure if trying to get segment 0 is enough or if this code should pass None/-1 to be parsed downstream
        #TODO: check with aliaksey
        request = VolumeRequest(source, id, 0, -100000, -100000, -100000, 100000, 100000, 100000, max_points)
        response = await volume_server.get_volume(request)

        # return {}
        return Response(response, headers={"Content-Disposition": f'attachment;filename="{id}.bcif"'})

    @app.get("/v2/{source}/{id}/metadata")
    async def get_metadata(
            source: str,
            id: str,
    ):
        request = MetadataRequest(source, id)
        metadata = await volume_server.get_metadata(request)

        return metadata

    @app.get("/v2/{source}/{id}/mesh/{segment_id}/{detail_lvl}")
    async def get_meshes(
            source: str,
            id: str,
            segment_id: int,
            detail_lvl: int
    ):
        request = MeshRequest(source, id, segment_id, detail_lvl)
        try:
            meshes = await volume_server.get_meshes(request)
            # return JSONResponse(str(meshes))  # JSONResponse(meshes) throws error
            return JSONNumpyResponse(meshes)  # JSONResponse(meshes) throws error
        except Exception as e:
            return JSONResponse({'error': str(e)}, status_code=HTTP_CODE_UNPROCESSABLE_ENTITY)

