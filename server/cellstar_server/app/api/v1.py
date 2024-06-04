from typing import Optional

from cellstar_db.file_system.annotations_context import AnnnotationsEditContext
from cellstar_db.file_system.db import FileSystemVolumeServerDB
from cellstar_db.models import (
    AnnotationsMetadata,
    DescriptionData,
    SegmentAnnotationData,
)
from cellstar_query.core.service import VolumeServerService
from cellstar_query.query import (
    HTTP_CODE_UNPROCESSABLE_ENTITY,
    get_geometric_segmentation_query,
    get_list_entries_keyword_query,
    get_list_entries_query,
    get_meshes_bcif_query,
    get_meshes_query,
    get_metadata_query,
    get_segmentation_box_query,
    get_segmentation_cell_query,
    get_volume_box_query,
    get_volume_cell_query,
    get_volume_info_query,
)
from cellstar_query.serialization.json_numpy_response import JSONNumpyResponse
from cellstar_server.app.settings import settings
from fastapi import Body, FastAPI, Query, Response
from starlette.responses import JSONResponse


def configure_endpoints(app: FastAPI, volume_server: VolumeServerService):
    # TODO: make it pydantic model for validation purposes
    @app.post("/v1/{source}/{id}/annotations_json/update")
    async def annotations_json_update(
        source: str,
        id: str,
        annotations_json: AnnotationsMetadata = Body(..., embed=True),
    ) -> None:
        db: FileSystemVolumeServerDB = volume_server.db
        # TODO: how to post entire json?
        # TODO: can annotations context be used for that?

        with db.edit_annotations(source, id) as ctx:
            ctx: AnnnotationsEditContext
            await ctx.update_annotations_json(annotations_json)

    @app.post("/v1/{source}/{id}/descriptions/edit")
    async def edit_descriptions_endpoint(
        source: str,
        id: str,
        descriptions: list[DescriptionData] = Body(..., embed=True),
    ) -> None:
        db: FileSystemVolumeServerDB = volume_server.db
        with db.edit_annotations(source, id) as ctx:
            ctx: AnnnotationsEditContext
            await ctx.add_or_modify_descriptions(descriptions)

    @app.post("/v1/{source}/{id}/segment_annotations/edit")
    async def edit_segment_annotations_endpoint(
        source: str,
        id: str,
        segment_annotations: list[SegmentAnnotationData] = Body(..., embed=True),
    ) -> None:
        db: FileSystemVolumeServerDB = volume_server.db
        with db.edit_annotations(source, id) as ctx:
            ctx: AnnnotationsEditContext
            await ctx.add_or_modify_segment_annotations(segment_annotations)

    @app.post("/v1/{source}/{id}/descriptions/remove")
    async def remove_descriptions_endpoint(
        source: str, id: str, description_ids: list[str] = Body(..., embed=True)
    ) -> None:
        db: FileSystemVolumeServerDB = volume_server.db
        with db.edit_annotations(source, id) as ctx:
            ctx: AnnnotationsEditContext
            await ctx.remove_descriptions(description_ids)

    @app.post("/v1/{source}/{id}/segment_annotations/remove")
    async def remove_segment_annotations_endpoint(
        source: str, id: str, annotation_ids: list[str] = Body(..., embed=True)
    ) -> None:
        db: FileSystemVolumeServerDB = volume_server.db
        with db.edit_annotations(source, id) as ctx:
            ctx: AnnnotationsEditContext
            await ctx.remove_segment_annotations(annotation_ids)

    @app.get("/v1/version")
    async def get_version():
        # settings = app.settings
        git_tag = settings.GIT_TAG
        git_sha = settings.GIT_SHA

        return {"git_tag": git_tag, "git_sha": git_sha}

    @app.get("/v1/list_entries/{limit}")
    async def get_entries(limit: int = 100):
        response = await get_list_entries_query(
            volume_server=volume_server, limit=limit
        )
        return response

    @app.get("/v1/list_entries/{limit}/{keyword}")
    async def get_entries_keyword(keyword: str, limit: int = 100):
        response = await get_list_entries_keyword_query(
            volume_server=volume_server, limit=limit, keyword=keyword
        )
        return response

    @app.get(
        "/v1/{source}/{id}/segmentation/box/{segmentation}/{time}/{a1}/{a2}/{a3}/{b1}/{b2}/{b3}"
    )
    async def get_segmentation_box(
        source: str,
        id: str,
        segmentation: str,
        time: int,
        a1: float,
        a2: float,
        a3: float,
        b1: float,
        b2: float,
        b3: float,
        max_points: Optional[int] = Query(0),
    ):
        response = await get_segmentation_box_query(
            volume_server=volume_server,
            source=source,
            id=id,
            segmentation_id=segmentation,
            time=time,
            a1=a1,
            a2=a2,
            a3=a3,
            b1=b1,
            b2=b2,
            b3=b3,
            max_points=max_points,
        )

        return Response(
            response,
            headers={"Content-Disposition": f'attachment;filename="{id}.bcif"'},
        )

    @app.get(
        "/v1/{source}/{id}/volume/box/{time}/{channel_id}/{a1}/{a2}/{a3}/{b1}/{b2}/{b3}"
    )
    async def get_volume_box(
        source: str,
        id: str,
        time: int,
        channel_id: str,
        a1: float,
        a2: float,
        a3: float,
        b1: float,
        b2: float,
        b3: float,
        max_points: Optional[int] = Query(0),
    ):
        response = await get_volume_box_query(
            volume_server=volume_server,
            source=source,
            id=id,
            time=time,
            channel_id=channel_id,
            a1=a1,
            a2=a2,
            a3=a3,
            b1=b1,
            b2=b2,
            b3=b3,
            max_points=max_points,
        )

        return Response(
            response,
            headers={"Content-Disposition": f'attachment;filename="{id}.bcif"'},
        )

    @app.get("/v1/{source}/{id}/segmentation/cell/{segmentation}/{time}")
    async def get_segmentation_cell(
        source: str,
        id: str,
        segmentation: str,
        time: int,
        max_points: Optional[int] = Query(0),
    ):
        response = await get_segmentation_cell_query(
            volume_server=volume_server,
            source=source,
            id=id,
            segmentation=segmentation,
            time=time,
            max_points=max_points,
        )

        return Response(
            response,
            headers={"Content-Disposition": f'attachment;filename="{id}.bcif"'},
        )

    @app.get("/v1/{source}/{id}/volume/cell/{time}/{channel_id}")
    async def get_volume_cell(
        source: str,
        id: str,
        time: int,
        channel_id: str,
        max_points: Optional[int] = Query(0),
    ):
        response = await get_volume_cell_query(
            volume_server=volume_server,
            source=source,
            id=id,
            time=time,
            channel_id=channel_id,
            max_points=max_points,
        )

        return Response(
            response,
            headers={"Content-Disposition": f'attachment;filename="{id}.bcif"'},
        )

    @app.get("/v1/{source}/{id}/metadata")
    async def get_metadata(
        source: str,
        id: str,
    ):
        metadata = await get_metadata_query(
            volume_server=volume_server, source=source, id=id
        )

        return metadata

    @app.get(
        "/v1/{source}/{id}/mesh/{segmentation_id}/{time}/{segment_id}/{detail_lvl}"
    )
    async def get_meshes(
        source: str,
        id: str,
        segmentation_id: str,
        time: int,
        segment_id: int,
        detail_lvl: int,
    ):
        try:
            response = await get_meshes_query(
                volume_server=volume_server,
                source=source,
                id=id,
                segmentation_id=segmentation_id,
                time=time,
                segment_id=segment_id,
                detail_lvl=detail_lvl,
            )
            return JSONNumpyResponse(response)
        except Exception as e:
            return JSONResponse(
                {"error": str(e)}, status_code=HTTP_CODE_UNPROCESSABLE_ENTITY
            )

    @app.get("/v1/{source}/{id}/geometric_segmentation/{segmentation_id}/{time}")
    async def get_geometric_segmentation(
        source: str, id: str, segmentation_id: str, time: int
    ):
        response = await get_geometric_segmentation_query(
            volume_server=volume_server,
            source=source,
            id=id,
            segmentation_id=segmentation_id,
            time=time,
        )
        return response

    @app.get("/v1/{source}/{id}/volume_info")
    async def get_volume_info(
        source: str,
        id: str,
    ):
        response_bytes = await get_volume_info_query(
            volume_server=volume_server, source=source, id=id
        )

        return Response(
            response_bytes,
            headers={
                "Content-Disposition": f'attachment;filename="{id}-volume_info.bcif"'
            },
        )

    @app.get(
        "/v1/{source}/{id}/mesh_bcif/{segmentation_id}/{time}/{segment_id}/{detail_lvl}"
    )
    async def get_meshes_bcif(
        source: str,
        id: str,
        segmentation_id: str,
        time: int,
        segment_id: int,
        detail_lvl: int,
    ):
        try:
            response_bytes = await get_meshes_bcif_query(
                volume_server=volume_server,
                source=source,
                id=id,
                segmentation_id=segmentation_id,
                time=time,
                segment_id=segment_id,
                detail_lvl=detail_lvl,
            )
            return Response(
                response_bytes,
                headers={
                    "Content-Disposition": f'attachment;filename="{id}-volume_info.bcif"'
                },
            )
        except Exception as e:
            return JSONResponse(
                {"error": str(e)}, status_code=HTTP_CODE_UNPROCESSABLE_ENTITY
            )
        finally:
            pass
