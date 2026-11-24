from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

class CitySlotResponse(BaseModel):
    id: str
    city: str
    date_str: str
    time_window: str
    status: str
    price_inr: int = 499
    max_capacity: int = 10
    seats_left: int = 5
    is_booked_by_user: bool = False

class BookSlotRequest(BaseModel):
    slot_id: str

class BookingResponse(BaseModel):
    booking_id: str
    slot_id: str
    date_str: str
    time_window: str
    status: str
    message: str
