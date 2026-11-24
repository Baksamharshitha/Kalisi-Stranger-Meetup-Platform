from typing import Optional
from pydantic import BaseModel

class UserRegister(BaseModel):
    full_name: str
    email: str
    password: str
    city: Optional[str] = "Chennai"

class UserLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    full_name: str
    city: str

class UserProfile(BaseModel):
    id: str
    full_name: str
    email: str
    city: str
    archetype: Optional[str] = None
    budget_tier: Optional[str] = None
