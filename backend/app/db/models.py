import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.db.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=True)
    age = Column(Integer, nullable=True)
    gender = Column(String, nullable=True)
    is_phone_verified = Column(Boolean, default=False)
    hashed_password = Column(String, nullable=False)
    city = Column(String, default="Chennai", index=True)
    is_verified = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    personality = relationship("PersonalityProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    preferences = relationship("DiningPreferences", back_populates="user", uselist=False, cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="user", cascade="all, delete-orphan")

class PersonalityProfile(Base):
    __tablename__ = "personality_profiles"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    archetype = Column(String, nullable=False)  # Clark Kent, Stark, Phoebe, Sherlock
    icebreaker_style = Column(String, nullable=True)
    answers_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="personality")

class DiningPreferences(Base):
    __tablename__ = "dining_preferences"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    budget_tier = Column(String, nullable=False)  # budget, mid_range, premium
    dietary_requirements = Column(String, default="No dietary restrictions")
    preferred_language = Column(String, default="English")
    updated_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="preferences")

class Restaurant(Base):
    __tablename__ = "restaurants"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    neighborhood = Column(String, nullable=False)  # e.g., Anna Nagar, Indiranagar
    full_address = Column(Text, nullable=False)
    cuisine = Column(String, nullable=False)
    price_tier = Column(String, nullable=False)
    city = Column(String, default="Chennai")
    
    # Detailed Venue Experience Metadata
    activities = Column(String, default="Curated conversation cards, table icebreakers, social games")
    duration_hours = Column(String, default="2.5 Hours (19:00 - 21:30)")
    special_features = Column(Text, default="Reserved private 6-person booth, quiet ambient acoustics, signature welcome drinks")
    contact_person = Column(String, default="Manager on Duty")
    contact_phone = Column(String, default="+91 98765 43210")

    tables = relationship("TableGroup", back_populates="restaurant")

class CitySlot(Base):
    __tablename__ = "city_slots"

    id = Column(String, primary_key=True, default=generate_uuid)
    title = Column(String, default="Weekend Stranger Dinner Meetup")
    city = Column(String, index=True, nullable=False)
    date_str = Column(String, nullable=False)  # e.g., "Sat, 11/28/2026"
    time_window = Column(String, nullable=False)  # e.g., "19:00 - 22:00"
    price_inr = Column(Integer, default=499)
    max_capacity = Column(Integer, default=10)  # Total seats available (e.g., 2 tables of 5)
    event_timestamp = Column(DateTime, nullable=False)
    status = Column(String, default="open")  # open, disabled, completed
    is_enabled = Column(Boolean, default=True)

    # Merged Venue & Event Details
    venue_name = Column(String, default="Curated Partner Restaurant")
    venue_address = Column(Text, default="Central City Location")
    about_event = Column(Text, default="Join 5 curated strangers for an evening of genuine conversations, delicious dining, and icebreaker games.")
    rules_and_regulations = Column(Text, default="1. Arrive within 15 minutes of start time.\n2. Equal bill splitting for food & drinks.\n3. Keep phone away and enjoy real conversations.\n4. Age 18+ verified diners only.")

    tables = relationship("TableGroup", back_populates="slot")
    bookings = relationship("Booking", back_populates="slot")

class TableGroup(Base):
    __tablename__ = "table_groups"

    id = Column(String, primary_key=True, default=generate_uuid)
    slot_id = Column(String, ForeignKey("city_slots.id", ondelete="CASCADE"), nullable=False)
    restaurant_id = Column(String, ForeignKey("restaurants.id"), nullable=True)
    table_number = Column(Integer, default=1)
    target_size = Column(Integer, default=5)
    archetype_summary = Column(String, nullable=True)  # "A mix of Clark Kent (3), Stark (2)..."
    reveal_stage = Column(String, default="locked")  # locked, area_revealed, fully_revealed

    slot = relationship("CitySlot", back_populates="tables")
    restaurant = relationship("Restaurant", back_populates="tables")
    bookings = relationship("Booking", back_populates="table")

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    slot_id = Column(String, ForeignKey("city_slots.id", ondelete="CASCADE"), nullable=False)
    table_id = Column(String, ForeignKey("table_groups.id"), nullable=True)
    booking_status = Column(String, default="confirmed")  # confirmed, cancelled, waitlist
    payment_status = Column(String, default="free_trial")  # free_trial, paid
    amount_paid = Column(Integer, default=0)
    payment_method = Column(String, default="Free Trial")  # Free Trial, Razorpay, UPI, Card
    payment_id = Column(String, default="FREE_TRIAL_PROMO")
    attendance_confirmed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="bookings")
    slot = relationship("CitySlot", back_populates="bookings")
    table = relationship("TableGroup", back_populates="bookings")

class TableFeedback(Base):
    __tablename__ = "table_feedback"

    id = Column(String, primary_key=True, default=generate_uuid)
    booking_id = Column(String, nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    vibe_rating = Column(Integer, nullable=False)  # 1-5
    food_rating = Column(Integer, nullable=False)  # 1-5
    comments = Column(Text, nullable=True)

class VideoReel(Base):
    __tablename__ = "video_reels"

    id = Column(String, primary_key=True, default=generate_uuid)
    title = Column(String, nullable=False)
    venue_name = Column(String, nullable=False)
    video_url = Column(String, nullable=False)
    thumbnail_url = Column(String, nullable=True)
    views_count = Column(Integer, default=1200)
    uploader_user_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    is_approved = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    uploader = relationship("User")

