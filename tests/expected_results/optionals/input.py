from enum import Enum
from typing import Optional, Union

import pydantic
from pydantic import BaseModel


class SomeEnum(str, Enum):
    a = "a"
    b = "b"


class SomeModel(BaseModel):
    some_optional: Optional[str]


class Foo(BaseModel):
    required: str

    default: str = "foo"
    default_factory: str = pydantic.Field(default_factory=lambda: "foo")
    default_alias: str = pydantic.Field("foo", alias="default_alias_renamed")

    optional: Optional[str]
    # TODO: This gets non-optional in output.ts, but should better be optional
    #       when assuming that null fields are removed from the JSON representation.
    optional_nullable: Optional[str] = pydantic.Field(..., nullable=True)
    optional_nullable_default: Optional[str] = pydantic.Field("foo", nullable=True)
    optional_nullable_default_none: Optional[str] = pydantic.Field(None, nullable=True)
    optional_default: Optional[str] = "foo"
    optional_default_none: Optional[str] = None
    union: Union[str, None]
    union_default: Union[str, None] = "foo"
    union_default_none: Union[str, None] = None
    optional_union: Union[int, Optional[str]]
    optional_union_default: Union[int, Optional[str]] = "foo"
    optional_union_default_none: Union[int, Optional[str]] = None

    # Force producing a schema definition without a module
    # to test the case where find_model() returns None.
    some_enum: SomeEnum

    some_optional_non_primitive: Optional[SomeModel]
