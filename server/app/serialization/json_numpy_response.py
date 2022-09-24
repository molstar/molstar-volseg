import json
import numpy
import fastapi
from typing import Any


class JSONNumpyResponse(fastapi.responses.JSONResponse):
    '''Behaves like FastAPI JSONResponse but allows content that contains numpy arrays (will be converted to lists)'''
    def render(self, content: Any) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
            cls=_NumpyJsonEncoder
        ).encode("utf-8")

class _NumpyJsonEncoder(json.JSONEncoder):
    '''Auxiliary class for JSON encoding of numpy arrays.'''
    def default(self, obj):
        if isinstance(obj, numpy.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)
