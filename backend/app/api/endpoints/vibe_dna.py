from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import User, PersonalityProfile
from app.schemas.vibe_dna import QuizQuestion, QuizSubmit, VibeDNAResult
from app.api.deps import get_current_user

router = APIRouter()

QUESTIONS: List[QuizQuestion] = [
    QuizQuestion(
        id="q1",
        question="How do you usually break the ice in a room full of strangers?",
        highlight="break the ice",
        options=["Humor", "Observation", "Listening", "Asking questions"]
    ),
    QuizQuestion(
        id="q2",
        question="What kind of conversations energize you most?",
        highlight="energize you most",
        options=["Deep life stories & philosophy", "Witty banter & pop culture", "Passionate debates on ideas", "Funny embarrassing moments"]
    ),
    QuizQuestion(
        id="q3",
        question="At a 5-person dinner table, your natural role is usually...",
        highlight="natural role",
        options=["The Spark (keeps energy high)", "The Anchor (makes everyone feel heard)", "The Wildcard (brings surprising stories)", "The Inquirer (asks insightful questions)"]
    )
]

ARCHETYPES = {
    "Humor": {
        "archetype": "Stark",
        "title": "The Charismatic Spark",
        "description": "Quick-witted, infectious energy, effortlessly brings laughter to the table.",
        "superpower": "Turns awkward silences into inside jokes within 60 seconds.",
        "icebreaker_style": "Humor & Wit"
    },
    "Listening": {
        "archetype": "Clark Kent",
        "title": "The Grounded Anchor",
        "description": "Warm, attentive, and genuinely curious. Makes everyone feel valued and comfortable.",
        "superpower": "Remembers the little details and makes people feel instantly safe.",
        "icebreaker_style": "Deep Listening"
    },
    "Observation": {
        "archetype": "Phoebe",
        "title": "The Creative Storyteller",
        "description": "Free-spirited, authentic, with a knack for unexpected and delightful anecdotes.",
        "superpower": "Notices what others miss and bridges completely different personalities.",
        "icebreaker_style": "Observation & Storytelling"
    },
    "Asking questions": {
        "archetype": "Sherlock",
        "title": "The Curious Inquirer",
        "description": "Thoughtful and insightful, loves exploring what makes people tick.",
        "superpower": "Asks the exact question that opens up someone's passion.",
        "icebreaker_style": "Curious Questions"
    }
}

@router.get("/quiz", response_model=List[QuizQuestion])
def get_quiz():
    return QUESTIONS

@router.post("/submit", response_model=VibeDNAResult)
def submit_quiz(data: QuizSubmit, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    icebreaker = data.answers.get("q1", "Listening")
    result_data = ARCHETYPES.get(icebreaker, ARCHETYPES["Listening"])
    
    # Save to user profile
    existing = db.query(PersonalityProfile).filter(PersonalityProfile.user_id == current_user.id).first()
    if existing:
        existing.archetype = result_data["archetype"]
        existing.icebreaker_style = result_data["icebreaker_style"]
        existing.answers_json = data.answers
    else:
        profile = PersonalityProfile(
            user_id=current_user.id,
            archetype=result_data["archetype"],
            icebreaker_style=result_data["icebreaker_style"],
            answers_json=data.answers
        )
        db.add(profile)
        
    db.commit()
    return VibeDNAResult(**result_data)
