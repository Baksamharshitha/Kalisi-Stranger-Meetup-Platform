from typing import Optional
from pydantic import BaseModel

class PreferencesUpdate(BaseModel):
    budget_tier: str  # budget, mid_range, premium
    dietary_requirements: Optional[str] = "No dietary restrictions"
    preferred_language: Optional[str] = "English"

class PreferencesResponse(BaseModel):
    user_id: str
    budget_tier: str
    dietary_requirements: str
    preferred_language: str
