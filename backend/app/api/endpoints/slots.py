from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.db.database import get_db
from app.db.models import User, CitySlot, Booking, TableGroup
from app.schemas.slots import CitySlotResponse, BookSlotRequest, BookingResponse
from app.api.deps import get_current_user
from app.services.matchmaking import cluster_slot_into_tables

router = APIRouter()

@router.get("/", response_model=List[CitySlotResponse])
def get_city_slots(
    city: str = Query("Central Bangalore"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    clean_city = city.strip()
    words = clean_city.split()
    primary_word = words[-1] if words else clean_city

    # Search with city exact match or substring or primary word
    slots = db.query(CitySlot).filter(
        or_(
            CitySlot.city.ilike(f"%{clean_city}%"),
            CitySlot.city.ilike(f"%{primary_word}%")
        )
    ).all()

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
            city=s.city,
            date_str=s.date_str,
            time_window=s.time_window,
            status=s.status,
            price_inr=s.price_inr or 499,
            max_capacity=capacity,
            seats_left=seats_left,
            is_booked_by_user=(s.id in user_bookings)
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
