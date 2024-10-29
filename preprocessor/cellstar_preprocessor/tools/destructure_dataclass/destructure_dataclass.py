from dataclasses import fields, is_dataclass
from typing import Callable, Dict, Optional, Protocol, TypedDict, Unpack

from pydantic import BaseModel

class DataclassProtocol(Protocol):
    __dataclass_fields__: Dict
    __dataclass_params__: Dict
    __post_init__: Optional[Callable]

def _destructure (d, *keys):
    return [ d[k] if k in d else None for k in keys ]

def destructure_dataclass(d: DataclassProtocol):
    fs = [field.name for field in fields(d)]
    return d[*fs]
    
    
class MyModel(BaseModel):
    a: int
    b: str


class MyDict(TypedDict):
    a: int
    b: str

# Unpack can be used for typing kwargs in function
def my_init(**kwargs: Unpack[MyDict]):
    return MyModel.model_validate(kwargs)
from typing_extensions import TypedDict
# How about
# 1. Switch from dataclass to Pydantic

# def unpack_pydantic_model(m: BaseModel):
#     d = m.model_dump()
#     d:
# # 2. model_dump_json => dict
# # 2.5 typeddict from pydantic model?
# # 3. unpack dict to variables
# 3.5 Use Unpack?
# 4. Return variables