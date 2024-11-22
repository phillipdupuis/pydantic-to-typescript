from typing import List

from pydantic import BaseModel

from .v2_animals.cats import Cat
from .v2_animals.dogs import Dog


class AnimalShelter(BaseModel):
    address: str
    cats: List[Cat]
    dogs: List[Dog]
