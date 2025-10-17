from pydantic import BaseModel, EmailStr

class Login(BaseModel):
    email: EmailStr
    password: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

class SimpleOk(BaseModel):
    ok: bool = True
