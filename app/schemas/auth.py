from datetime import datetime

from pydantic import BaseModel, Field, EmailStr

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)

class UserRegisterResponse(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime

class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=25)

class TokenResponse(BaseModel):
    access_token:str
    token_type:str