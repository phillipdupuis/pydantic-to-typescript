from enum import Enum

try:
    from pydantic.v1 import BaseModel
except ImportError:
    from pydantic import BaseModel


class DogBreed(str, Enum):
    mutt = "mutt"
    labrador = "labrador"
    golden_retriever = "golden retriever"


class Dog(BaseModel):
    name: str
    age: int
    breed: DogBreed
