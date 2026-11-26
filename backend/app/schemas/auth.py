from typing import Optional, Dict, Any
from pydantic import BaseModel

class UserRegister(BaseModel):
    full_name: str
    email: str
    password: str
    city: Optional[str] = "Hyderabad"
    phone: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    full_name: str
    city: str
    archetype: Optional[str] = None
    title: Optional[str] = None
    superpower: Optional[str] = None

class UserProfile(BaseModel):
    id: str
    full_name: str
    email: str
    city: str
    phone: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    archetype: Optional[str] = None
    budget_tier: Optional[str] = None

class SendOTPRequest(BaseModel):
    phone: str

class VerifyOTPRequest(BaseModel):
    phone: str
    otp: str

class OTPResponse(BaseModel):
    status: str
    message: str
    dev_otp: Optional[str] = None

class OnboardingSignupRequest(BaseModel):
    full_name: str
    age: int
    gender: str
    city: str
    phone: str
    otp: str
    answers: Dict[str, Any]
    email: Optional[str] = None
    password: Optional[str] = "kalisi2026"

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class UploadVideoRequest(BaseModel):
    title: str
    venue_name: str
    video_url: str
    thumbnail_url: Optional[str] = None

