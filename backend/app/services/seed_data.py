from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.db.models import Restaurant, CitySlot, User, PersonalityProfile, DiningPreferences, TableGroup, Booking, VideoReel
from app.core.security import get_password_hash

def seed_database(db: Session):
    # Check if already seeded
    if db.query(Restaurant).first():
        return

    # Seed Rich Verified Restaurants
    r1 = Restaurant(
        name="Chamber of Potions Anna Nagar",
        neighborhood="Anna Nagar",
        full_address="C10, Ravilla Towers, Anna Nagar 3rd Main Rd, W Block, Anna Nagar, Chennai, Tamil Nadu 600040",
        cuisine="Italian / Continental",
        price_tier="mid_range",
        city="Chennai",
        activities="Table-side icebreaker card deck, social trivia round, dedicated host introduction",
        duration_hours="2.5 Hours (19:00 - 21:30)",
        special_features="Private corner 6-person booth, moody ambient potion-themed lighting, complimentary artisan mocktail",
        contact_person="Ramesh (Partner Operations)",
        contact_phone="+91 98400 12345"
    )
    r2 = Restaurant(
        name="Ciclo Cafe Kotturpuram",
        neighborhood="Kotturpuram",
        full_address="47, Gandhi Mandapam Rd, Chitra Nagar, Kotturpuram, Chennai, Tamil Nadu 600085",
        cuisine="European & Artisanal Bakery",
        price_tier="budget",
        city="Chennai",
        activities="Coffee tasting quiz, travel story exchange, light acoustic background",
        duration_hours="2.0 Hours (19:00 - 21:00)",
        special_features="Open garden courtyard table, heritage cycling aesthetic, hand-drip single origin brews",
        contact_person="Priya Anand",
        contact_phone="+91 98401 54321"
    )
    r3 = Restaurant(
        name="The Fatty Bao Indiranagar",
        neighborhood="Indiranagar",
        full_address="610, 12th Main Rd, 7th Cross, HAL 2nd Stage, Indiranagar, Bengaluru, Karnataka 560038",
        cuisine="Asian & Dim Sum",
        price_tier="premium",
        city="Bangalore",
        activities="Chef's mystery bao tasting, rapid-fire vibe match questions",
        duration_hours="3.0 Hours (20:00 - 23:00)",
        special_features="Rooftop terrace seating with panoramic skyline view, exclusive mixology pairings",
        contact_person="Vikram Rao",
        contact_phone="+91 98800 99887"
    )
    db.add_all([r1, r2, r3])
    db.flush()

    # Seed City Slots with Capacity and Pricing
    base_date = datetime.utcnow() + timedelta(days=2)
    s1 = CitySlot(
        city="Chennai",
        date_str="Sat, 11/28/2026",
        time_window="19:00 - 22:00",
        price_inr=499,
        max_capacity=10,  # 2 tables of 5
        event_timestamp=base_date,
        status="open"
    )
    s2 = CitySlot(
        city="Chennai",
        date_str="Sun, 11/29/2026",
        time_window="20:00 - 23:00",
        price_inr=499,
        max_capacity=10,
        event_timestamp=base_date + timedelta(days=1),
        status="open"
    )
    s3 = CitySlot(
        city="Chennai",
        date_str="Sat, 12/05/2026",
        time_window="19:00 - 22:00",
        price_inr=599,
        max_capacity=10,
        event_timestamp=base_date + timedelta(days=7),
        status="open"
    )
    s4 = CitySlot(
        city="Central Bangalore",
        date_str="Sat, 11/28/2026",
        time_window="19:00 - 22:00",
        price_inr=599,
        max_capacity=10,
        event_timestamp=base_date,
        status="open"
    )
    s5 = CitySlot(
        city="Central Bangalore",
        date_str="Sun, 11/29/2026",
        time_window="20:00 - 23:00",
        price_inr=599,
        max_capacity=10,
        event_timestamp=base_date + timedelta(days=1),
        status="open"
    )
    s6 = CitySlot(
        city="Indiranagar Bangalore",
        date_str="Sat, 12/05/2026",
        time_window="19:30 - 22:30",
        price_inr=699,
        max_capacity=10,
        event_timestamp=base_date + timedelta(days=7),
        status="open"
    )
    s_past1 = CitySlot(
        city="Hyderabad",
        date_str="Sat, 11/14/2026",
        time_window="19:00 - 22:00",
        price_inr=499,
        max_capacity=10,
        event_timestamp=base_date - timedelta(days=14),
        status="completed"
    )
    s_past2 = CitySlot(
        city="Bangalore",
        date_str="Sun, 11/15/2026",
        time_window="20:00 - 23:00",
        price_inr=599,
        max_capacity=10,
        event_timestamp=base_date - timedelta(days=13),
        status="completed"
    )
    db.add_all([s1, s2, s3, s4, s5, s6, s_past1, s_past2])
    db.flush()

    # Seed Video Reels for Community & App
    vr1 = VideoReel(
        title="First 5 Mins vs Last 5 Mins at Kalisi",
        venue_name="Chamber of Potions, Anna Nagar",
        video_url="https://www.w3schools.com/html/mov_bbb.mp4",
        thumbnail_url="https://images.unsplash.com/photo-1543007630-9710e4a00a20?auto=format&fit=crop&w=800&q=80",
        views_count=14200,
        is_approved=True
    )
    vr2 = VideoReel(
        title="What Happens When 5 Introverts Dine Together?",
        venue_name="Central Bangalore Meetup",
        video_url="https://www.w3schools.com/html/mov_bbb.mp4",
        thumbnail_url="https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=800&q=80",
        views_count=28500,
        is_approved=True
    )
    vr3 = VideoReel(
        title="The Mystery Menu Taste Test with Strangers",
        venue_name="The Fatty Bao, Indiranagar",
        video_url="https://www.w3schools.com/html/mov_bbb.mp4",
        thumbnail_url="https://images.unsplash.com/photo-1514933651103-005eec06c04b?auto=format&fit=crop&w=800&q=80",
        views_count=9800,
        is_approved=True
    )
    db.add_all([vr1, vr2, vr3])
    db.flush()

    # Create demo strangers to populate Table #1 for s1
    mock_users = [
        ("Gautham", "gautham@example.com", "Clark Kent", "mid_range", "Free Trial", 0),
        ("Adithya", "adithya@example.com", "Stark", "mid_range", "Razorpay UPI", 499),
        ("Riya", "riya@example.com", "Phoebe", "mid_range", "Credit Card", 499),
        ("Kavya", "kavya@example.com", "Clark Kent", "mid_range", "Free Trial", 0),
    ]
    
    mock_bookings = []
    for idx, (name, email, arch, tier, pay_method, amt) in enumerate(mock_users):
        u = User(
            full_name=name,
            email=email,
            hashed_password=get_password_hash("password123"),
            city="Chennai"
        )
        db.add(u)
        db.flush()
        
        p = PersonalityProfile(
            user_id=u.id,
            archetype=arch,
            icebreaker_style="Humor" if arch == "Stark" else "Listening"
        )
        db.add(p)
        
        pref = DiningPreferences(
            user_id=u.id,
            budget_tier=tier,
            dietary_requirements="No dietary restrictions"
        )
        db.add(pref)
        
        b = Booking(
            user_id=u.id,
            slot_id=s1.id,
            booking_status="confirmed",
            payment_status="paid" if amt > 0 else "free_trial",
            amount_paid=amt,
            payment_method=pay_method,
            payment_id=f"pay_demo_{1000 + idx}"
        )
        db.add(b)
        db.flush()
        mock_bookings.append(b)
        
    # Create Table #1 with pre-filled strangers
    table = TableGroup(
        slot_id=s1.id,
        restaurant_id=r1.id,
        table_number=1,
        target_size=5,
        archetype_summary="A mix of Clark Kent (2), Stark (1), and Phoebe (1)",
        reveal_stage="fully_revealed"
    )
    db.add(table)
    db.flush()
    
    for b in mock_bookings:
        b.table_id = table.id

    db.commit()
