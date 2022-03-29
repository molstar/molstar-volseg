from volume_server.requests.volume_request.i_volume_request import IVolumeRequest


class VolumeRequest(IVolumeRequest):
    def __init__(self,
                 source: str,
                 structure_id: str,
                 segmentation_id: int,
                 x_min: float,
                 y_min: float,
                 z_min: float,
                 x_max: float,
                 y_max: float,
                 z_max: float,
                 max_size_kb: int
                 ):
        self._source = source
        self._structure_id = structure_id
        self._segmentation_id = segmentation_id
        self._x_min = x_min
        self._y_min = y_min
        self._z_min = z_min
        self._x_max = x_max
        self._y_max = y_max
        self._z_max = z_max
        self._max_size_kb = max_size_kb

    def source(self) -> str:
        return self._source

    def structure_id(self) -> str:
        return self._structure_id

    def segmentation_id(self) -> int:
        return self._segmentation_id

    def x_min(self) -> float:
        return self._x_min

    def x_max(self) -> float:
        return self._x_max

    def y_min(self) -> float:
        return self._y_min

    def y_max(self) -> float:
        return self._y_max

    def z_min(self) -> float:
        return self._z_min

    def z_max(self) -> float:
        return self._z_max

    def max_size_kb(self) -> int:
        return self._max_size_kb

