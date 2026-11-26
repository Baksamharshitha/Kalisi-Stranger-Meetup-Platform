from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

class CitySlotResponse(BaseModel):
    id: str
    title: str = "Weekend Stranger Dinner Meetup"
    city: str
    date_str: str
    time_window: str
    status: str
    price_inr: int = 499
    max_capacity: int = 10
    seats_left: int = 5
    is_booked_by_user: bool = False
    is_enabled: bool = True
    venue_name: Optional[str] = "Curated Partner Restaurant"
    venue_address: Optional[str] = "Central City Location"
    about_event: Optional[str] = "Join 5 curated strangers for an evening of genuine conversations, delicious dining, and icebreaker games."
    rules_and_regulations: Optional[str] = "1. Arrive within 15 minutes of start time.\n2. Equal bill splitting for food & drinks.\n3. Keep phone away and enjoy real conversations.\n4. Age 18+ verified diners only."

class BookSlotRequest(BaseModel):
    slot_id: str

class BookingResponse(BaseModel):
    booking_id: str
    slot_id: str
    date_str: str
    time_window: str
    status: str
    message: str
