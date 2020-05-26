from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional

api = FastAPI()


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


@api.post('/login/', response_model=LoginResponseData)
def login(body: LoginCredentials):
    profile = Profile(**body.dict(), age=72, hobbies=['cats'])
    return LoginResponseData(token='very-secure', profile=profile)
