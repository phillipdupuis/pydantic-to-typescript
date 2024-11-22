from typing import List

try:
    from pydantic.v1 import BaseModel
except ImportError:
    from pydantic import BaseModel

from .v1_animals.cats import Cat
from .v1_animals.dogs import Dog


class AnimalShelter(BaseModel):
    address: str
    cats: List[Cat]
    dogs: List[Dog]
