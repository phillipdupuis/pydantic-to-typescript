from pydantic import BaseModel
from typing import List
from .animals.cats import Cat
from .animals.dogs import Dog


class AnimalShelter(BaseModel):
    address: str
    cats: List[Cat]
    dogs: List[Dog]
