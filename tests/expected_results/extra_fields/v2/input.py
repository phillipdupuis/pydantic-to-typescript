from pydantic import BaseModel, ConfigDict


class ModelExtraAllow(BaseModel):
    model_config = ConfigDict(extra="allow")
    a: str


class ModelExtraForbid(BaseModel):
    model_config = ConfigDict(extra="forbid")
    a: str


class ModelExtraIgnore(BaseModel):
    model_config = ConfigDict(extra="ignore")
    a: str


class ModelExtraNone(BaseModel):
    a: str
