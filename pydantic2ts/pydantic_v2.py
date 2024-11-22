try:
    from pydantic.version import VERSION

    assert VERSION.startswith("2")

    from pydantic import BaseModel, create_model

    enabled = True
except (ImportError, AssertionError, AttributeError):
    BaseModel = None
    create_model = None
    enabled = False

__all__ = ("BaseModel", "create_model", "enabled")
