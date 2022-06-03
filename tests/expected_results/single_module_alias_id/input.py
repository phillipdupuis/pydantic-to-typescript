from pydantic import BaseModel, Field
from typing import Optional, List


class LoginCredentials(BaseModel):
    username: str
    password: str


class Profile(BaseModel):
    id: int = Field(..., alias='_id', 
        description="Appears in model without the underscore, but stored with it.")
    username: str
    age: Optional[int]
    hobbies: List[str]


class LoginResponseData(BaseModel):
    token: str
    profile: Profile
