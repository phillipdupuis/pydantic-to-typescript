from pydantic import BaseModel
from typing import Optional, Literal
from enum import Enum


class CatBreed(str, Enum):
    domestic_shorthair = "domestic shorthair"
    bengal = "bengal"
    persian = "persian"
    siamese = "siamese"


class Cat(BaseModel):
    name: str
    age: int
    declawed: bool
    breed: CatBreed
