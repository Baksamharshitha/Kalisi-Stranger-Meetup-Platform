from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.db.database import get_db
from app.db.models import User, CitySlot, Booking, TableGroup
from app.schemas.slots import CitySlotResponse, BookSlotRequest, BookingResponse
from app.api.deps import get_current_user, get_current_user_optional
from app.services.matchmaking import cluster_slot_into_tables

router = APIRouter()

@router.get("/locations", response_model=List[str])
def get_available_locations(db: Session = Depends(get_db)):
    """Return distinct active city locations from database slots, with standard curated defaults."""
    rows = db.query(CitySlot.city).filter(CitySlot.city.isnot(None)).distinct().all()
    found = [r[0].strip() for r in rows if r[0] and r[0].strip()]
    defaults = [
        "Central Bangalore",
        "Indiranagar Bangalore",
        "Koramangala Bangalore",
        "Anna Nagar Chennai",
        "South Mumbai",
    ]
    for d in defaults:
        if d not in found:
            found.append(d)
    return found

@router.get("/", response_model=List[CitySlotResponse])
def get_city_slots(
    city: str = Query("Central Bangalore"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    clean_city = city.strip().lower()

    # Query only slots for the selected location (strict neighborhood filter)
    all_open_slots = db.query(CitySlot).filter(CitySlot.status == "open").all()
    slots = []
    for s in all_open_slots:
        slot_city = (s.city or "").strip().lower()
        # Direct exact or strict neighborhood match
        if clean_city == slot_city or clean_city in slot_city or slot_city in clean_city:
            # Prevent cross-matching between different Bangalore neighborhoods
            if "indiranagar" in clean_city and "indiranagar" not in slot_city:
                continue
            if "koramangala" in clean_city and "koramangala" not in slot_city:
                continue
            if "central" in clean_city and "central" not in slot_city:
                continue
            slots.append(s)

    user_bookings = set()
    if current_user:
        user_bookings = {
            b.slot_id for b in db.query(Booking).filter(
                Booking.user_id == current_user.id,
                Booking.booking_status == "confirmed"
            ).all()
        }
    
    res = []
    for s in slots:
        capacity = s.max_capacity or 10
        booked = len(s.bookings)
        seats_left = max(0, capacity - booked)
        
        res.append(CitySlotResponse(
            id=s.id,
            title=getattr(s, "title", None) or f"{s.city} Stranger Dinner Meetup",
            city=s.city,
            date_str=s.date_str,
            time_window=s.time_window,
            status=s.status,
            price_inr=s.price_inr or 499,
            max_capacity=capacity,
            seats_left=seats_left,
            is_booked_by_user=(s.id in user_bookings),
            is_enabled=(s.status == "open"),
            venue_name=getattr(s, "venue_name", None) or "Curated Partner Restaurant",
            venue_address=getattr(s, "venue_address", None) or f"Central {s.city} Location",
            about_event=getattr(s, "about_event", None) or "Join 5 curated strangers for an evening of genuine conversations, delicious dining, and icebreaker games.",
            rules_and_regulations=getattr(s, "rules_and_regulations", None) or "1. Arrive within 15 minutes of start time.\n2. Equal bill splitting for food & drinks.\n3. Keep phone away and enjoy real conversations.\n4. Age 18+ verified diners only."
        ))
    return res

@router.post("/book", response_model=BookingResponse)
def book_slot(
    req: BookSlotRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    slot = db.query(CitySlot).filter(CitySlot.id == req.slot_id).first()
    if not slot:
        raise HTTPException(status_code=404, detail="City slot not found")
        
    existing = db.query(Booking).filter(
        Booking.user_id == current_user.id,
        Booking.slot_id == req.slot_id,
        Booking.booking_status == "confirmed"
    ).first()
    if existing:
        return BookingResponse(
            booking_id=existing.id,
            slot_id=slot.id,
            date_str=slot.date_str,
            time_window=slot.time_window,
            status=existing.booking_status,
            message="You are already confirmed for this dinner slot!"
        )
        
    booking = Booking(
        user_id=current_user.id,
        slot_id=slot.id,
        booking_status="confirmed",
        payment_status="paid",
        amount_paid=slot.price_inr or 499,
        payment_method="UPI / Razorpay"
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    
    cluster_slot_into_tables(db, slot.id)
    
    return BookingResponse(
        booking_id=booking.id,
        slot_id=slot.id,
        date_str=slot.date_str,
        time_window=slot.time_window,
        status="confirmed",
        message="Your seat is locked! Table reveal begins progressively."
    )
