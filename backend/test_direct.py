import sys
import os

# Ensure backend directory is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.database import SessionLocal, Base, engine
from app.services.seed_data import seed_database
from app.schemas.auth import UserRegister, UserLogin
from app.schemas.vibe_dna import QuizSubmit
from app.schemas.preferences import PreferencesUpdate
from app.schemas.slots import BookSlotRequest
from app.api.endpoints import auth, vibe_dna, preferences, slots, reveal
from app.db.models import User

def run_tests():
    print("Initializing Database...")
    Base.metadata.create_all(bind=engine)
    
    with SessionLocal() as db:
        seed_database(db)
        print("✓ Database Seeded Successfully")

        # 1. Test Registration
        email = "rajesh_direct@example.com"
        # Cleanup if exists
        old = db.query(User).filter(User.email == email).first()
        if old:
            db.delete(old)
            db.commit()

        reg_data = UserRegister(
            full_name="Rajesh Kumar",
            email=email,
            password="securepassword123",
            city="Chennai"
        )
        token_res = auth.register(reg_data, db=db)
        assert token_res.access_token is not None
        user_id = token_res.user_id
        current_user = db.query(User).filter(User.id == user_id).first()
        print(f"✓ User Registration Passed: {current_user.full_name} ({current_user.city})")

        # 2. Test Vibe DNA Quiz
        questions = vibe_dna.get_quiz()
        assert len(questions) >= 3
        print(f"✓ Vibe DNA Quiz Retrieval Passed: {len(questions)} questions")

        submit_data = QuizSubmit(answers={
            "q1": "Humor",
            "q2": "Witty banter & pop culture",
            "q3": "The Spark (keeps energy high)"
        })
        vibe_result = vibe_dna.submit_quiz(submit_data, current_user=current_user, db=db)
        assert vibe_result.archetype == "Stark"
        print(f"✓ Vibe DNA Matching Passed: Classified as '{vibe_result.archetype}' - {vibe_result.title}")

        # 3. Test Dining Preferences Customization
        pref_data = PreferencesUpdate(
            budget_tier="mid_range",
            dietary_requirements="Vegetarian",
            preferred_language="English"
        )
        pref_result = preferences.update_preferences(pref_data, current_user=current_user, db=db)
        assert pref_result.budget_tier == "mid_range"
        print(f"✓ Dining Preferences Passed: {pref_result.budget_tier}, {pref_result.dietary_requirements}")

        # 4. Test City Slots Discovery
        available_slots = slots.get_city_slots(city="Chennai", current_user=current_user, db=db)
        assert len(available_slots) > 0
        target_slot = available_slots[0]
        print(f"✓ City Slots Loaded: {len(available_slots)} upcoming slots in Chennai")

        # 5. Test Slot Booking
        book_req = BookSlotRequest(slot_id=target_slot.id)
        book_res = slots.book_slot(book_req, current_user=current_user, db=db)
        assert book_res.booking_id is not None
        print(f"✓ Booking Confirmed: Booking ID = {book_res.booking_id}")

        # 6. Test Progressive Reveal
        reveal_data = reveal.get_progressive_reveal(book_res.booking_id, current_user=current_user, db=db)
        assert reveal_data.reveal_stage in ["locked", "area_revealed", "fully_revealed"]
        print(f"✓ Progressive Reveal State: '{reveal_data.reveal_stage}'")
        print(f"  Neighborhood: {reveal_data.neighborhood}")
        print(f"  Restaurant: {reveal_data.restaurant_name}")
        print(f"  Table Number: {reveal_data.table_number}")
        print(f"  Group Archetype Teaser: {reveal_data.group_summary}")
        print(f"  Character Insights Loaded: {len(reveal_data.character_insights or [])}")

    print("\n" + "="*50)
    print("ALL 6 CORE BACKEND PIPELINE TESTS PASSED!")
    print("="*50)

if __name__ == "__main__":
    run_tests()
