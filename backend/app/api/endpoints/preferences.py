from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import User, DiningPreferences
from app.schemas.preferences import PreferencesUpdate, PreferencesResponse
from app.api.deps import get_current_user

router = APIRouter()

@router.put("/update", response_model=PreferencesResponse)
def update_preferences(
    data: PreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    pref = db.query(DiningPreferences).filter(DiningPreferences.user_id == current_user.id).first()
    if pref:
        pref.budget_tier = data.budget_tier
        pref.dietary_requirements = data.dietary_requirements
        pref.preferred_language = data.preferred_language
    else:
        pref = DiningPreferences(
            user_id=current_user.id,
            budget_tier=data.budget_tier,
            dietary_requirements=data.dietary_requirements,
            preferred_language=data.preferred_language
        )
        db.add(pref)
        
    db.commit()
    return PreferencesResponse(
        user_id=current_user.id,
        budget_tier=pref.budget_tier,
        dietary_requirements=pref.dietary_requirements,
        preferred_language=pref.preferred_language
    )

@router.get("/me", response_model=PreferencesResponse)
def get_my_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    pref = db.query(DiningPreferences).filter(DiningPreferences.user_id == current_user.id).first()
    if not pref:
        return PreferencesResponse(
            user_id=current_user.id,
            budget_tier="mid_range",
            dietary_requirements="No dietary restrictions",
            preferred_language="English"
        )
    return PreferencesResponse(
        user_id=current_user.id,
        budget_tier=pref.budget_tier,
        dietary_requirements=pref.dietary_requirements,
        preferred_language=pref.preferred_language
    )
