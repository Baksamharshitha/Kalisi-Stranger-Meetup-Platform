import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from app.main import app

@pytest.fixture
def anyio_backend():
    return 'asyncio'

@pytest.mark.anyio
async def test_root():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["app"] == "Kalisi API"
        assert "Five Strangers" in data["tagline"]

@pytest.mark.anyio
async def test_full_user_journey():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Register
        user_email = "testuser_kalisi@example.com"
        reg_res = await client.post("/api/auth/register", json={
            "full_name": "Karthik Raja",
            "email": user_email,
            "password": "mypassword123",
            "city": "Chennai"
        })
        if reg_res.status_code == 200:
            token = reg_res.json()["access_token"]
        else:
            login_res = await client.post("/api/auth/login", json={
                "email": user_email,
                "password": "mypassword123"
            })
            assert login_res.status_code == 200
            token = login_res.json()["access_token"]

        headers = {"Authorization": f"Bearer {token}"}

        # 2. Get Vibe DNA Quiz
        quiz_res = await client.get("/api/vibe-dna/quiz")
        assert quiz_res.status_code == 200
        questions = quiz_res.json()
        assert len(questions) >= 3

        # 3. Submit Vibe DNA Quiz -> get archetype
        submit_res = await client.post("/api/vibe-dna/submit", headers=headers, json={
            "answers": {
                "q1": "Humor",
                "q2": "Witty banter & pop culture",
                "q3": "The Spark (keeps energy high)"
            }
        })
        assert submit_res.status_code == 200
        vibe_data = submit_res.json()
        assert vibe_data["archetype"] == "Stark"

        # 4. Customize Dining Preferences
        pref_res = await client.put("/api/preferences/update", headers=headers, json={
            "budget_tier": "mid_range",
            "dietary_requirements": "Vegetarian",
            "preferred_language": "English"
        })
        assert pref_res.status_code == 200
        assert pref_res.json()["budget_tier"] == "mid_range"

        # 5. Fetch City Slots for Chennai
        slots_res = await client.get("/api/slots/?city=Chennai", headers=headers)
        assert slots_res.status_code == 200
        slots = slots_res.json()
        assert len(slots) >= 1
        selected_slot = slots[0]

        # 6. Book Slot
        book_res = await client.post("/api/slots/book", headers=headers, json={
            "slot_id": selected_slot["id"]
        })
        assert book_res.status_code == 200
        booking = book_res.json()
        booking_id = booking["booking_id"]

        # 7. Progressive Reveal
        reveal_res = await client.get(f"/api/reveal/{booking_id}", headers=headers)
        assert reveal_res.status_code == 200
        reveal = reveal_res.json()
        assert reveal["reveal_stage"] in ["locked", "area_revealed", "fully_revealed"]
        if reveal["reveal_stage"] == "fully_revealed":
            assert reveal["table_number"] is not None
            assert "Chamber of Potions" in reveal["restaurant_name"]
            assert len(reveal["character_insights"]) > 0
