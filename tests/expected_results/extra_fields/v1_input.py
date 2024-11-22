try:
    from pydantic.v1 import BaseConfig, BaseModel, Extra
except ImportError:
    from pydantic import BaseConfig, BaseModel, Extra


class ModelExtraAllow(BaseModel):
    a: str

    class Config(BaseConfig):
        extra = Extra.allow


class ModelExtraForbid(BaseModel):
    a: str

    class Config(BaseConfig):
        extra = Extra.forbid


class ModelExtraIgnore(BaseModel):
    a: str

    class Config(BaseConfig):
        extra = Extra.ignore


class ModelExtraNone(BaseModel):
    a: str
