from app.requests.mesh_request.i_mesh_request import IMeshRequest


class MeshRequest(IMeshRequest):
    def __init__(self,
                 source: str,
                 id: str,
                 segment_id: int,
                 detail_lvl: int
                 ):
        self._source = source
        self._id = id
        self._segment_id = segment_id
        self._detail_lvl = detail_lvl

    def source(self) -> str:
        return self._source

    def id(self) -> str:
        return self._id

    def segment_id(self) -> int:
        return self._segment_id

    def detail_lvl(self) -> int:
        return self._detail_lvl

