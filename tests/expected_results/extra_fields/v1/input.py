from pydantic import BaseModel, Extra


class ModelAllow(BaseModel, extra=Extra.allow):
    a: str

class ModelDefault(BaseModel):
    a: str

