'''
Extension to the API used for debugging purposes (for mesh visualization in frontend)
'''
from collections import defaultdict

from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse

from volume_server.src.i_volume_server import IVolumeServer
from volume_server.src.requests.metadata_request.metadata_request import MetadataRequest
from volume_server.src.requests.volume_request.volume_request import VolumeRequest
from db.interface.i_preprocessed_db import IReadOnlyPreprocessedDb  # .local_disk.local_disk_preprocessed_db import LocalDiskPreprocessedDb
from db.interface.i_preprocessed_medatada import IPreprocessedMetadata
from db.implementations.local_disk.local_disk_preprocessed_db import ReadContext
from .json_numpy_response import JSONNumpyResponse


HTTP_CODE_UNPROCESSABLE_ENTITY = 422


def configure_endpoints(app: FastAPI, db: IReadOnlyPreprocessedDb):
    @app.get("/v1/{source}/{id}/mesh/{segment_id}/{detail_lvl}")
    async def get_mesh(
            source: str,
            id: str,
            segment_id: int,
            detail_lvl: int
    ):
        context: ReadContext
        with db.read(source, id) as context:
            try:
                meshes = await context.read_meshes(segment_id=segment_id, detail_lvl=detail_lvl)
            except KeyError as ex:
                meta = await db.read_metadata(source, id)
                segments_levels = _extract_segments_detail_levels(meta)
                error_msg = f'Invalid segment_id={segment_id} or detail_lvl={detail_lvl} (available segment_ids and detail_lvls: {segments_levels})'
                return JSONResponse({'error': error_msg}, status_code=HTTP_CODE_UNPROCESSABLE_ENTITY)
        return JSONNumpyResponse(meshes)
    

def _extract_segments_detail_levels(meta: IPreprocessedMetadata) -> dict[int, list[int]]:
    '''Extract available segment_ids and detail_lvls for each segment_id'''
    meta_js = meta.json_metadata()
    segments_levels = meta_js.get('segmentation_meshes', {}).get('mesh_component_numbers', {}).get('segment_ids', {})
    result: dict[int, list[int]] = defaultdict(list)
    for seg, obj in segments_levels.items():
        for lvl in obj.get('detail_lvls', {}).keys():
            result[int(seg)].append(int(lvl))
    sorted_result = { seg: sorted(result[seg]) for seg in sorted(result.keys()) }
    return sorted_result
