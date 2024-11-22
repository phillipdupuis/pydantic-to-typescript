from typing import List, Optional

from pydantic import BaseModel


class LoginCredentials(BaseModel):
    username: str
    password: str


class Profile(BaseModel):
    username: str
    age: Optional[int] = None
    hobbies: List[str]


class LoginResponseData(BaseModel):
    token: str
    profile: Profile
