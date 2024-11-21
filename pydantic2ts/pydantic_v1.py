try:
    from pydantic.v1 import BaseModel, create_model  # type: ignore
    from pydantic.v1.generics import GenericModel

    enabled = True
except ImportError:
    from pydantic import BaseModel, create_model

    enabled = True

    try:
        from pydantic.generics import GenericModel
    except ImportError:  # pragma: no cover
        GenericModel = None

__all__ = ("BaseModel", "GenericModel", "create_model", "enabled")
