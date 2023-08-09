from typing import List

from pydantic import BaseModel

from .animals.cats import Cat
from .animals.dogs import Dog


class AnimalShelter(BaseModel):
    address: str
    cats: List[Cat]
    dogs: List[Dog]
