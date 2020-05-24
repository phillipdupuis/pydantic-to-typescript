from pydantic import BaseModel, Extra
from enum import Enum
from typing import List


class NoUnspecifiedProps:
    extra = Extra.forbid


class Sport(str, Enum):
    football = 'football'
    basketball = 'basketball'
    running = 'running'
    swimming = 'swimming'


class Athlete(BaseModel):
    name: str
    age: int
    sports: List[Sport]
    Config = NoUnspecifiedProps


class Team(BaseModel):
    name: str
    sport: Sport
    athletes: List[Athlete]
    Config = NoUnspecifiedProps
