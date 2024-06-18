from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from src.models.models import Role

# from src.routes.auth import refresh_token


class UserSchema(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: str = EmailStr
    password: str = Field(min_length=6, max_length=8)


class UserResponse(BaseModel):
    id: int = 1
    username: str
    email: EmailStr
    avatar: str
    role: Role
    model_config = ConfigDict(from_attributes=True)


class TokenSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class RequestEmail(BaseModel):
    email: EmailStr
    
class ResetPasswordSchema(BaseModel):
    password: str = Field(min_length=6, max_length=8)
