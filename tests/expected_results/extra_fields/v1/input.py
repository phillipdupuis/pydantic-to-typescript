try:
    from pydantic.v1 import BaseModel, Extra
except ImportError:
    from pydantic import BaseModel, Extra


class ModelAllow(BaseModel, extra=Extra.allow):
    a: str


class ModelDefault(BaseModel):
    a: str
