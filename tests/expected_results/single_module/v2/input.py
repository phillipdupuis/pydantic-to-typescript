from pydantic import BaseModel
from typing import Optional, List


class LoginCredentials(BaseModel):
    username: str
    password: str


class Profile(BaseModel):
    username: str
    age: Optional[int]
    hobbies: List[str]


class LoginResponseData(BaseModel):
    token: str
    profile: Profile
