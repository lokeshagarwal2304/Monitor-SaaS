from typing import Optional
from pydantic import BaseModel, EmailStr, validator

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    email: Optional[EmailStr] = None
    
    @validator('email')
    def email_must_be_lowercase(cls, v):
        if v:
            return v.lower()
        return v