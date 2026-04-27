from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginData(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    role: str


class UserProfileData(BaseModel):
    id: int
    username: str
    role: str
