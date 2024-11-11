from typing import List, Optional

try:
    from pydantic.v1 import BaseModel
except ImportError:
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
