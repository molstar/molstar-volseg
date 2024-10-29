from cellstar_query.core.service import VolumeServerService
from cellstar_query.requests import (
    EntriesRequest,
    GeometricSegmentationRequest,
    MeshRequest,
    InfoRequest,
    VolumeRequestBox,
    VolumeRequestDataKind,
    VolumeRequestInfo,
)
from db.cellstar_db.models import Info

HTTP_CODE_UNPROCESSABLE_ENTITY = 422


async def get_segmentation_box_query(
    volume_server: VolumeServerService,
    source: str,
    id: str,
    segmentation_id: str,
    time: int,
    a1: float,
    a2: float,
    a3: float,
    b1: float,
    b2: float,
    b3: float,
    max_points: int,
):
    response = await volume_server.get_volume_data(
        req=VolumeRequestInfo(
            source=source,
            structure_id=id,
            segmentation_id=segmentation_id,
            time=time,
            max_points=max_points,
            data_kind=VolumeRequestDataKind.segmentation,
        ),
        req_box=VolumeRequestBox(bottom_left=(a1, a2, a3), top_right=(b1, b2, b3)),
    )
    return response


async def get_volume_box_query(
    volume_server: VolumeServerService,
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
    max_points: int,
):
    response = await volume_server.get_volume_data(
        req=VolumeRequestInfo(
            source=source,
            structure_id=id,
            channel_id=channel_id,
            time=time,
            max_points=max_points,
            data_kind=VolumeRequestDataKind.volume,
        ),
        req_box=VolumeRequestBox(bottom_left=(a1, a2, a3), top_right=(b1, b2, b3)),
    )
    return response


async def get_segmentation_cell_query(
    volume_server: VolumeServerService,
    source: str,
    id: str,
    segmentation: str,
    time: int,
    max_points: int,
):
    response = await volume_server.get_volume_data(
        req=VolumeRequestInfo(
            source=source,
            structure_id=id,
            segmentation_id=segmentation,
            time=time,
            max_points=max_points,
            data_kind=VolumeRequestDataKind.segmentation,
        ),
    )

    return response


async def get_volume_cell_query(
    volume_server: VolumeServerService,
    source: str,
    id: str,
    time: int,
    channel_id: str,
    max_points: int,
):
    response = await volume_server.get_volume_data(
        req=VolumeRequestInfo(
            source=source,
            structure_id=id,
            time=time,
            channel_id=channel_id,
            max_points=max_points,
            data_kind=VolumeRequestDataKind.volume,
        ),
    )

    return response


async def get_info_query(
    volume_server: VolumeServerService,
    id: str,
    source: str,
) -> Info:
    request = InfoRequest(source=source, structure_id=id)
    metadata = await volume_server.get_info(request)
    return metadata.model_dump()


async def get_volume_info_query(
    volume_server: VolumeServerService,
    id: str,
    source: str,
):
    request = InfoRequest(source=source, structure_id=id)
    response_bytes = await volume_server.get_volume_info(request)

    return response_bytes


async def get_list_entries_query(volume_server: VolumeServerService, limit: int):
    request = EntriesRequest(limit=limit, keyword="")
    response = await volume_server.get_entries(request)

    return response


async def get_list_entries_keyword_query(
    volume_server: VolumeServerService, limit: int, keyword: str
):
    request = EntriesRequest(limit=limit, keyword=keyword)
    response = await volume_server.get_entries(request)
    return response


async def get_meshes_query(
    volume_server: VolumeServerService,
    source: str,
    id: str,
    segmentation_id: str,
    time: int,
    segment_id: int,
    detail_lvl: int,
):
    request = MeshRequest(
        source=source,
        structure_id=id,
        segmentation_id=segmentation_id,
        segment_id=segment_id,
        detail_lvl=detail_lvl,
        time=time,
    )
    meshes = await volume_server.get_meshes(request)
    return meshes


async def get_meshes_bcif_query(
    volume_server: VolumeServerService,
    source: str,
    id: str,
    segmentation_id: str,
    time: int,
    segment_id: int,
    detail_lvl: int,
):
    request = MeshRequest(
        source=source,
        structure_id=id,
        segmentation_id=segmentation_id,
        segment_id=segment_id,
        detail_lvl=detail_lvl,
        time=time,
    )

    response_bytes = await volume_server.get_meshes_bcif(request)
    return response_bytes


async def get_geometric_segmentation_query(
    volume_server: VolumeServerService,
    source: str,
    id: str,
    segmentation_id: str,
    time: int,
):
    request = GeometricSegmentationRequest(
        source=source, structure_id=id, segmentation_id=segmentation_id, time=time
    )
    geometric_segmentation = await volume_server.get_geometric_segmentation(request)
    return geometric_segmentation
