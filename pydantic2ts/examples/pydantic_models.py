from pydantic import BaseModel, Extra
from enum import Enum
from typing import List, Dict


class NoExtraProps:
    extra = Extra.forbid


class Sport(str, Enum):
    football = 'football'
    basketball = 'basketball'


class Athlete(BaseModel):
    name: str
    age: int
    sports: List[Sport]
    Config = NoExtraProps


class Team(BaseModel):
    name: str
    sport: Sport
    athletes: List[Athlete]
    Config = NoExtraProps


class League(BaseModel):
    cities: Dict[str, Team]
    Config = NoExtraProps
