import json
from typing import Optional

from fastapi import FastAPI, Response
from starlette.responses import JSONResponse

from app.api.service import VolumeServerService
from app.requests.entries_request.entries_request import EntriesRequest
from app.requests.mesh_request.mesh_request import MeshRequest
from app.requests.metadata_request.metadata_request import MetadataRequest
from .json_numpy_response import JSONNumpyResponse

from app.requests.volume import VolumeRequestInfo, VolumeRequestBox

HTTP_CODE_UNPROCESSABLE_ENTITY = 422


def configure_endpoints(app: FastAPI, volume_server: VolumeServerService):
    @app.get("/v1/list_entries/{limit}")
    async def get_entries(
            limit: int = 100
    ):
        request = EntriesRequest(limit, "")
        response = await volume_server.get_entries(request)

        return response

    @app.get("/v1/list_entries/{limit}/{keyword}")
    async def get_entries_keyword(
            keyword: str,
            limit: int = 100
    ):
        request = EntriesRequest(limit, keyword)
        response = await volume_server.get_entries(request)

        return response

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
        response = await volume_server.get_volume_data(
            req=VolumeRequestInfo(source=source, structure_id=id, segmentation_id=segmentation, max_points=max_points, data_kind="all"),
            req_box=VolumeRequestBox(bottom_left=(a1, a2, a3), top_right=(b1, b2, b3))
        )

        return Response(response, headers={"Content-Disposition": f'attachment;filename="{id}.bcif"'})

    @app.get("/v1/{source}/{id}/cell/{segmentation}/{max_points}")
    async def get_cell(
            source: str,
            id: str,
            segmentation: int,
            max_points: Optional[int] = 0
    ):
        response = await volume_server.get_volume_data(
            req=VolumeRequestInfo(source=source, structure_id=id, segmentation_id=segmentation, max_points=max_points, data_kind="all")
        )

        return Response(response, headers={"Content-Disposition": f'attachment;filename="{id}.bcif"'})

    @app.get("/v1/{source}/{id}/metadata")
    async def get_metadata(
            source: str,
            id: str,
    ):
        request = MetadataRequest(source, id)
        metadata = await volume_server.get_metadata(request)

        return metadata

    @app.get("/v1/{source}/{id}/mesh/{segment_id}/{detail_lvl}")
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

