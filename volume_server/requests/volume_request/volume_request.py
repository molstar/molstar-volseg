from volume_server.requests.volume_request.i_volume_request import IVolumeRequest


class VolumeRequest(IVolumeRequest):
    def __init__(self,
                 source: str,
                 structure_id: str,
                 x_min: int = -1,
                 y_min: int = -1,
                 z_min: int = -1,
                 x_max: int = -1,
                 y_max: int = -1,
                 z_max: int = -1
                 ):
        self._source = source
        self._structure_id = structure_id
        self._x_min = x_min
        self._y_min = y_min
        self._z_min = z_min
        self._x_max = x_max
        self._y_max = y_max
        self._z_max = z_max

    def source(self) -> str:
        return self._source

    def structure_id(self) -> str:
        return self._structure_id

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

