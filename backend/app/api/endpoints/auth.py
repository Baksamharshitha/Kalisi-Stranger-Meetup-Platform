import random
import re
from typing import Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import User, PersonalityProfile, DiningPreferences, Booking, CitySlot, VideoReel
from app.schemas.auth import (
    UserRegister, UserLogin, Token, UserProfile,
    SendOTPRequest, VerifyOTPRequest, OTPResponse, OnboardingSignupRequest,
    ChangePasswordRequest, UploadVideoRequest
)
from app.core.security import get_password_hash, verify_password, create_access_token
from app.api.deps import get_current_user
from app.api.endpoints.vibe_dna import calculate_archetype

router = APIRouter()

# In-memory OTP storage for dev & testing: phone -> 6-digit OTP
OTP_STORE: Dict[str, str] = {}

@router.post("/send-otp", response_model=OTPResponse)
def send_otp(req: SendOTPRequest):
    phone_clean = re.sub(r"\D", "", req.phone)
    if len(phone_clean) < 10:
        raise HTTPException(status_code=400, detail="Please enter a valid 10-digit mobile number")
    
    # Generate 6-digit code (dev default: 123456 or random)
    otp_code = str(random.randint(100000, 999999))
    # We also allow 123456 as master bypass for easy testing
    OTP_STORE[phone_clean] = otp_code

    print(f"======================================================")
    print(f"📱 KALISI OTP SMS DISPATCH: Phone={phone_clean} OTP={otp_code}")
    print(f"======================================================")

    return OTPResponse(
        status="success",
        message=f"6-digit verification code sent to +91 {phone_clean[-10:]}",
        dev_otp=otp_code
    )

@router.post("/verify-otp", response_model=OTPResponse)
def verify_otp(req: VerifyOTPRequest):
    phone_clean = re.sub(r"\D", "", req.phone)
    stored = OTP_STORE.get(phone_clean)
    
    # Allow actual generated OTP or universal testing code 123456
    if req.otp == stored or req.otp == "123456":
        return OTPResponse(status="success", message="Mobile number verified successfully!")
    raise HTTPException(status_code=400, detail="Invalid verification code. Please check or use code 123456")

@router.post("/onboarding-complete", response_model=Token)
def onboarding_complete(req: OnboardingSignupRequest, db: Session = Depends(get_db)):
    phone_clean = re.sub(r"\D", "", req.phone)
    stored = OTP_STORE.get(phone_clean)
    
    # Validate OTP
    if req.otp != stored and req.otp != "123456":
        raise HTTPException(status_code=400, detail="Invalid OTP code. Please verify your mobile number.")

    email = req.email or f"user_{phone_clean[-10:]}@kalisi.app"
    password = req.password or "kalisi2026"

    # Check existing user
    user = db.query(User).filter((User.phone == phone_clean) | (User.email == email)).first()
    if not user:
        user = User(
            full_name=req.full_name,
            email=email,
            phone=phone_clean,
            age=req.age,
            gender=req.gender,
            city=req.city or "Hyderabad",
            hashed_password=get_password_hash(password),
            is_phone_verified=True,
            is_verified=True
        )
        db.add(user)
        db.flush()
    else:
        user.full_name = req.full_name
        user.age = req.age
        user.gender = req.gender
        user.city = req.city
        user.phone = phone_clean
        user.is_phone_verified = True

    # 1. Compute Vibe DNA Archetype from the 15 quiz answers
    vibe_result = calculate_archetype(req.answers)

    # 2. Save/Update Personality Profile
    profile = db.query(PersonalityProfile).filter(PersonalityProfile.user_id == user.id).first()
    if profile:
        profile.archetype = vibe_result["archetype"]
        profile.icebreaker_style = vibe_result["icebreaker_style"]
        profile.answers_json = req.answers
    else:
        profile = PersonalityProfile(
            user_id=user.id,
            archetype=vibe_result["archetype"],
            icebreaker_style=vibe_result["icebreaker_style"],
            answers_json=req.answers
        )
        db.add(profile)

    # 3. Save/Update Dining Preferences
    dietary = str(req.answers.get("dietary_preference", "Vegetarian"))
    budget_raw = str(req.answers.get("dinner_budget", "Mid-Range"))
    budget_tier = "mid_range"
    if "under" in budget_raw.lower(): budget_tier = "budget"
    elif "2,000" in budget_raw.lower() or "luxury" in budget_raw.lower(): budget_tier = "premium"

    pref = db.query(DiningPreferences).filter(DiningPreferences.user_id == user.id).first()
    if pref:
        pref.dietary_requirements = dietary
        pref.budget_tier = budget_tier
    else:
        pref = DiningPreferences(
            user_id=user.id,
            budget_tier=budget_tier,
            dietary_requirements=dietary,
            preferred_language="English"
        )
        db.add(pref)

    db.commit()
    db.refresh(user)

    token = create_access_token(user.id)
    return Token(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        full_name=user.full_name,
        city=user.city,
        archetype=vibe_result["archetype"],
        title=vibe_result["title"],
        superpower=vibe_result["superpower"]
    )

@router.post("/register", response_model=Token)
def register(user_in: UserRegister, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        full_name=user_in.full_name,
        email=user_in.email,
        phone=user_in.phone,
        age=user_in.age,
        gender=user_in.gender,
        hashed_password=get_password_hash(user_in.password),
        city=user_in.city or "Hyderabad"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id)
    return Token(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        full_name=user.full_name,
        city=user.city
    )

@router.post("/login", response_model=Token)
def login(user_in: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_in.email).first()
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    token = create_access_token(user.id)
    arch = user.personality.archetype if user.personality else "Stark"
    return Token(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        full_name=user.full_name,
        city=user.city,
        archetype=arch
    )

@router.get("/me", response_model=UserProfile)
def get_me(current_user: User = Depends(get_current_user)):
    archetype = current_user.personality.archetype if current_user.personality else None
    budget_tier = current_user.preferences.budget_tier if current_user.preferences else None
    return UserProfile(
        id=current_user.id,
        full_name=current_user.full_name,
        email=current_user.email,
        city=current_user.city,
        phone=current_user.phone,
        age=current_user.age,
        gender=current_user.gender,
        archetype=archetype,
        budget_tier=budget_tier
    )

@router.put("/change-password")
def change_password(
    req: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not verify_password(req.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if len(req.new_password) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters")
    
    current_user.hashed_password = get_password_hash(req.new_password)
    db.commit()
    return {"status": "success", "message": "Password updated successfully"}

@router.delete("/delete-account")
def delete_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db.delete(current_user)
    db.commit()
    return {"status": "success", "message": "Account deleted permanently"}

@router.get("/user-bookings")
def get_user_bookings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    bookings = db.query(Booking).filter(
        Booking.user_id == current_user.id,
        Booking.booking_status == "confirmed"
    ).all()

    booked = []
    attended = []

    for b in bookings:
        slot = b.slot
        item = {
            "booking_id": b.id,
            "slot_id": slot.id if slot else "",
            "city": slot.city if slot else "",
            "date_str": slot.date_str if slot else "",
            "time_window": slot.time_window if slot else "",
            "price_inr": slot.price_inr if slot else 499,
            "table_number": b.table.table_number if b.table else 1,
            "restaurant_name": b.table.restaurant.name if (b.table and b.table.restaurant) else "Curated Mystery Venue",
            "restaurant_address": b.table.restaurant.full_address if (b.table and b.table.restaurant) else "Address revealed on dinner day",
            "amount_paid": b.amount_paid or 0,
            "payment_status": b.payment_status,
            "payment_method": b.payment_method,
            "created_at": b.created_at.strftime("%Y-%m-%d %H:%M") if b.created_at else "",
        }
        if (slot and slot.status == "completed") or b.attendance_confirmed:
            attended.append(item)
        else:
            booked.append(item)

    return {"booked": booked, "attended": attended}

@router.get("/user-videos")
def get_user_videos(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    uploaded = db.query(VideoReel).filter(VideoReel.uploader_user_id == current_user.id).all()
    community = db.query(VideoReel).filter(VideoReel.is_approved == True).order_by(VideoReel.views_count.desc()).limit(10).all()

    def format_v(v):
        return {
            "id": v.id,
            "title": v.title,
            "venue": v.venue_name,
            "video_url": v.video_url,
            "thumbnail_url": v.thumbnail_url or "https://images.unsplash.com/photo-1543007630-9710e4a00a20?auto=format&fit=crop&w=800&q=80",
            "views": f"{v.views_count // 1000}K views" if v.views_count >= 1000 else f"{v.views_count} views",
            "created_at": v.created_at.strftime("%Y-%m-%d") if v.created_at else "Recent"
        }

    return {
        "uploaded": [format_v(v) for v in uploaded],
        "community": [format_v(v) for v in community]
    }

@router.post("/upload-video")
def upload_video(
    req: UploadVideoRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    video = VideoReel(
        title=req.title,
        venue_name=req.venue_name,
        video_url=req.video_url,
        thumbnail_url=req.thumbnail_url or "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=800&q=80",
        uploader_user_id=current_user.id,
        is_approved=True
    )
    db.add(video)
    db.commit()
    return {
        "status": "success",
        "message": "Dinner memory video uploaded successfully!",
        "video_id": video.id
    }

