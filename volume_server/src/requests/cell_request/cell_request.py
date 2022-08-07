from volume_server.src.requests.cell_request.i_cell_request import ICellRequest


class CellRequest(ICellRequest):
    def __init__(self,
                 source: str,
                 structure_id: str,
                 segmentation_id: int,
                 max_points: int
                 ):
        self._source = source
        self._structure_id = structure_id
        self._segmentation_id = segmentation_id
        self._max_points = max_points

    def source(self) -> str:
        return self._source

    def structure_id(self) -> str:
        return self._structure_id

    def segmentation_id(self) -> int:
        return self._segmentation_id

    def max_points(self) -> int:
        return self._max_points

