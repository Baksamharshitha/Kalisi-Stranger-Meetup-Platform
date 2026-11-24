from typing import List, Dict
from sqlalchemy.orm import Session
from app.db.models import Booking, TableGroup, Restaurant, PersonalityProfile, DiningPreferences

ARCHETYPE_DESCRIPTIONS = {
    "Clark Kent": {
        "vibe": "The grounded, warm listener who puts everyone at ease.",
        "starter": "Ask about their favorite hidden spot in the city or their calmest Sunday memory."
    },
    "Stark": {
        "vibe": "The charismatic spark who brings quick wit, energy, and laughs.",
        "starter": "Ask what ambitious, slightly crazy project they'd fund with unlimited cash."
    },
    "Phoebe": {
        "vibe": "The creative storyteller with quirky experiences and unexpected insights.",
        "starter": "Ask for the most surreal or serendipitous encounter they've ever had."
    },
    "Sherlock": {
        "vibe": "The curious inquirer who asks thought-provoking, deep-dive questions.",
        "starter": "Ask what unsolved mystery or deep truth they spend the most time pondering."
    }
}

def cluster_slot_into_tables(db: Session, slot_id: str):
    """
    Groups bookings for a slot into tables of 4-6 (ideal target: 5 strangers).
    Matches on budget tier and balances conversational archetypes.
    """
    unassigned_bookings = (
        db.query(Booking)
        .filter(Booking.slot_id == slot_id, Booking.table_id == None, Booking.booking_status == "confirmed")
        .all()
    )
    
    if len(unassigned_bookings) < 4:
        # Need at least 4 to form a Kalisi table
        return
    
    # Group bookings by user budget tier
    tier_groups: Dict[str, List[Booking]] = {}
    for b in unassigned_bookings:
        pref = db.query(DiningPreferences).filter(DiningPreferences.user_id == b.user_id).first()
        tier = pref.budget_tier if pref else "mid_range"
        tier_groups.setdefault(tier, []).append(b)
        
    for tier, bookings in tier_groups.items():
        while len(bookings) >= 4:
            table_batch = bookings[:5]
            bookings = bookings[5:]
            
            # Find matching restaurant
            restaurant = db.query(Restaurant).filter(Restaurant.price_tier == tier).first()
            if not restaurant:
                restaurant = db.query(Restaurant).first()
                
            # Count archetypes
            counts: Dict[str, int] = {}
            for b in table_batch:
                profile = db.query(PersonalityProfile).filter(PersonalityProfile.user_id == b.user_id).first()
                arch = profile.archetype if profile else "Clark Kent"
                counts[arch] = counts.get(arch, 0) + 1
                
            summary_parts = [f"{arch} ({cnt})" for arch, cnt in counts.items()]
            summary_text = "A mix of " + ", ".join(summary_parts)
            
            # Create table
            existing_tables = db.query(TableGroup).filter(TableGroup.slot_id == slot_id).count()
            table = TableGroup(
                slot_id=slot_id,
                restaurant_id=restaurant.id if restaurant else None,
                table_number=existing_tables + 1,
                target_size=len(table_batch),
                archetype_summary=summary_text,
                reveal_stage="fully_revealed"  # Ready to reveal
            )
            db.add(table)
            db.flush()
            
            for b in table_batch:
                b.table_id = table.id
                
    db.commit()
