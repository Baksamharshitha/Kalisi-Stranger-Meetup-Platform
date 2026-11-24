from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import User, Booking, TableGroup, Restaurant
from app.schemas.reveal import ProgressiveRevealResponse, CharacterInsight
from app.api.deps import get_current_user
from app.services.matchmaking import ARCHETYPE_DESCRIPTIONS

router = APIRouter()

@router.get("/{booking_id}", response_model=ProgressiveRevealResponse)
def get_progressive_reveal(
    booking_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    booking = db.query(Booking).filter(Booking.id == booking_id, Booking.user_id == current_user.id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    slot = booking.slot
    table = booking.table
    
    # If not yet assigned to a table, return State 1: Locked
    if not table:
        return ProgressiveRevealResponse(
            booking_id=booking.id,
            reveal_stage="locked",
            date_str=slot.date_str,
            time_window=slot.time_window,
            city=slot.city
        )

    restaurant = table.restaurant
    
    insights: List[CharacterInsight] = []
    # Build character insights from table summary
    for arch, meta in ARCHETYPE_DESCRIPTIONS.items():
        insights.append(CharacterInsight(
            archetype=arch,
            count=1 if arch in (table.archetype_summary or "") else 0,
            vibe_description=meta["vibe"],
            conversation_starter=meta["starter"]
        ))
        
    return ProgressiveRevealResponse(
        booking_id=booking.id,
        reveal_stage=table.reveal_stage,
        date_str=slot.date_str,
        time_window=slot.time_window,
        city=slot.city,
        neighborhood=restaurant.neighborhood if restaurant else "Anna Nagar",
        table_number=table.table_number,
        restaurant_name=restaurant.name if restaurant else "Chamber of Potions Anna Nagar",
        restaurant_address=restaurant.full_address if restaurant else "Anna Nagar, Chennai",
        cuisine=restaurant.cuisine if restaurant else "Italian / Continental",
        group_summary=table.archetype_summary or "A mix of Clark Kent (2), Stark (2), and Phoebe (1)",
        character_insights=insights
    )
