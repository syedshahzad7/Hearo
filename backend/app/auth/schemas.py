from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None
    role: str = "student"  # or "professional"

class UserPublic(BaseModel):
    id: str
    email: EmailStr
    full_name: str | None = None
    role: str

class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: str  # user id

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
