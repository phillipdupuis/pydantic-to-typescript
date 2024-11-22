# https://docs.pydantic.dev/latest/usage/computed_fields/

from pydantic import BaseModel, computed_field


class Rectangle(BaseModel):
    width: int
    length: int

    @computed_field
    @property
    def area(self) -> int:
        return self.width * self.length
