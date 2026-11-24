from typing import Optional, List, Dict
from pydantic import BaseModel

class CharacterInsight(BaseModel):
    archetype: str
    count: int
    vibe_description: str
    conversation_starter: str

class ProgressiveRevealResponse(BaseModel):
    booking_id: str
    reveal_stage: str  # locked, area_revealed, fully_revealed
    date_str: str
    time_window: str
    city: str
    
    # Area level (T-24h)
    neighborhood: Optional[str] = None
    
    # Full level (Day of Event)
    table_number: Optional[int] = None
    restaurant_name: Optional[str] = None
    restaurant_address: Optional[str] = None
    cuisine: Optional[str] = None
    group_summary: Optional[str] = None
    character_insights: Optional[List[CharacterInsight]] = None
