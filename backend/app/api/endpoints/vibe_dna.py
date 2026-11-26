from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import User, PersonalityProfile, DiningPreferences
from app.schemas.vibe_dna import QuizQuestion, QuizSubmit, VibeDNAResult
from app.api.deps import get_current_user

router = APIRouter()

ONBOARDING_20_QUESTIONS: List[QuizQuestion] = [
    # Q1: Fixed - Full Name
    QuizQuestion(
        id="full_name",
        question="What's your full name?",
        subtitle="How should your tablemates and the host address you?",
        highlight="full name",
        type="text",
        options=[],
        category="identity"
    ),
    # Q2: Fixed - Age
    QuizQuestion(
        id="age",
        question="How old are you?",
        subtitle="Helps us curate comfortable, peer-aligned tables.",
        highlight="old are you",
        type="age",
        options=["18-22", "23-27", "28-34", "35-42", "43+"],
        category="identity"
    ),
    # Q3: Fixed - Gender
    QuizQuestion(
        id="gender",
        question="What's your gender?",
        subtitle="Ensures balanced, inclusive dinner groups.",
        highlight="your gender",
        type="single_choice",
        options=["Male", "Female", "Non-binary", "Prefer not to say"],
        category="identity"
    ),
    # Q4: Fixed - Location / City
    QuizQuestion(
        id="city",
        question="Which city are you currently in?",
        subtitle="Where would you like to attend stranger dinners?",
        highlight="city",
        type="single_choice",
        options=["Hyderabad", "Bangalore", "Chennai", "Mumbai"],
        category="identity"
    ),
    # Q5: Set 1 & 2 - Purpose
    QuizQuestion(
        id="intent",
        question="What brings you to Kalisi?",
        subtitle="Your main intention for dining with five strangers.",
        highlight="brings you",
        type="single_choice",
        options=[
            "Make genuine new friends",
            "Share great conversations & food",
            "Step out of my comfort zone",
            "Try new unique dining experiences"
        ],
        category="vibe"
    ),
    # Q6: Set 1 - Friend's Perspective
    QuizQuestion(
        id="friend_description",
        question="How would your closest friends describe you?",
        subtitle="Your natural aura around people who know you best.",
        highlight="describe you",
        type="single_choice",
        options=[
            "The witty spark who brings laughs",
            "The calm anchor who keeps things grounded",
            "The adventurous soul ready for anything",
            "The thoughtful listener with deep insights"
        ],
        category="vibe"
    ),
    # Q7: Set 1 - Icebreaker approach
    QuizQuestion(
        id="approach_strangers",
        question="How do you approach a room full of strangers?",
        subtitle="Your signature way to break the ice.",
        highlight="approach strangers",
        type="single_choice",
        options=[
            "Say hello with an open smile",
            "Crack a lighthearted witty joke",
            "Observe the room first, then jump in",
            "Wait for someone to start the conversation"
        ],
        category="vibe"
    ),
    # Q8: Set 1 - Conversation style
    QuizQuestion(
        id="conversation_style",
        question="What's your preferred conversation style?",
        subtitle="The kind of dialogues that keep you hooked all evening.",
        highlight="conversation style",
        type="single_choice",
        options=[
            "Witty banter & rapid pop-culture humor",
            "Deep life stories, philosophies & dreams",
            "Curious questions & uncovering passions",
            "Random rabbit holes & quirky observations"
        ],
        category="social"
    ),
    # Q9: Set 1 - Group role
    QuizQuestion(
        id="group_role",
        question="At a 5-person dinner table, your natural energy is…",
        subtitle="The unique role you effortlessly step into.",
        highlight="natural energy",
        type="single_choice",
        options=[
            "The Spark (keeps energy high & laughter alive)",
            "The Anchor (makes everyone feel heard & safe)",
            "The Storyteller (brings unexpected real-life stories)",
            "The Inquirer (asks thoughtful, fascinating questions)"
        ],
        category="social"
    ),
    # Q10: Set 2 - Handling awkward silences
    QuizQuestion(
        id="awkward_silences",
        question="How do you handle an awkward pause at the table?",
        subtitle="When the conversation momentarily drops...",
        highlight="awkward silences",
        type="single_choice",
        options=[
            "Drop a humorous self-deprecating comment",
            "Ask a wild, intriguing hypothetical question",
            "Comfortably sip my drink and let it be",
            "Smoothly introduce a fresh, exciting topic"
        ],
        category="social"
    ),
    # Q11: Set 1 - Social battery recharge
    QuizQuestion(
        id="recharge_style",
        question="How does your social battery recharge best?",
        subtitle="After an eventful, engaging weekend...",
        highlight="social battery",
        type="single_choice",
        options=[
            "Solo quiet time with books or a movie",
            "Putting on headphones and vibing to music",
            "Low-key hangout with 1 or 2 close friends",
            "Deep uninterrupted 9-hour sleep"
        ],
        category="social"
    ),
    # Q12: Set 1 & 3 - Spontaneity scale
    QuizQuestion(
        id="spontaneity",
        question="How spontaneous are you when plans change?",
        subtitle="Your comfort with surprise twists and turns.",
        highlight="spontaneous",
        type="single_choice",
        options=[
            "A structured planner (I like knowing what's next)",
            "Balanced & flexible (I easily go with the flow)",
            "Wildly spontaneous (Say yes first, figure it out later!)"
        ],
        category="vibe"
    ),
    # Q13: Set 2 & 3 - Favorite topics
    QuizQuestion(
        id="favorite_topic",
        question="What topic energizes you most at a dinner table?",
        subtitle="The subject that makes you lose track of time.",
        highlight="energizes you most",
        type="single_choice",
        options=[
            "Travel tales, bucket lists & wild road trips",
            "Cinema, music, books & pop culture debates",
            "Big ideas, startup stories & personal ambitions",
            "Food culture, secret recipes & culinary gems"
        ],
        category="entertainment"
    ),
    # Q14: Set 3 - Time machine era
    QuizQuestion(
        id="time_machine_era",
        question="If you had a time machine for one dinner, which era would you revisit?",
        subtitle="A nostalgic peek into your inner aesthetic.",
        highlight="time machine",
        type="single_choice",
        options=[
            "The Retro 80s (Synthwave, neon & disco grooves)",
            "The Golden 90s (Cartoons, pop icons & mixtapes)",
            "The Indie 2000s (Early internet, pop-punk & cafe culture)",
            "The Futuristic 2050 (Cyberpunk, sci-fi & flying cars)"
        ],
        category="entertainment"
    ),
    # Q15: Set 3 - Table activity
    QuizQuestion(
        id="table_activity",
        question="Which table activity would you pick for the table?",
        subtitle="An icebreaker format to spark connection.",
        highlight="table activity",
        type="single_choice",
        options=[
            "Table card deck with spicy, thoughtful dilemmas",
            "Hilarious social party games & rapid trivia",
            "Anthakshari & guessing nostalgic song intros",
            "Chef's mystery food tasting & flavor rating"
        ],
        category="entertainment"
    ),
    # Q16: Set 3 - Ideal meetup setting
    QuizQuestion(
        id="ideal_setting",
        question="Pick your ideal dinner meetup setting.",
        subtitle="The ambiance that gives you the best vibes.",
        highlight="ideal meetup",
        type="single_choice",
        options=[
            "Breezy rooftop with panoramic city skyline",
            "Warm, candlelit boutique café with cozy booths",
            "Buzzing modern bistro with craft kitchen vibes",
            "Hidden speakeasy with moody ambient jazz"
        ],
        category="taste"
    ),
    # Q17: Set 3 - Go-to comfort cuisine
    QuizQuestion(
        id="favorite_cuisine",
        question="What's your go-to comfort cuisine?",
        subtitle="What makes your tastebuds happiest?",
        highlight="comfort cuisine",
        type="single_choice",
        options=[
            "Authentic Indian & aromatic Biryanis",
            "Italian handmade pastas & artisan woodfired pizzas",
            "Pan-Asian ramen, sushi & steamed dim sum",
            "Mexican tacos, nachos & vibrant continental"
        ],
        category="taste"
    ),
    # Q18: Set 1, 2 & 3 - Dietary preference
    QuizQuestion(
        id="dietary_preference",
        question="What is your dietary preference?",
        subtitle="Essential for reserving the right restaurant menu.",
        highlight="dietary preference",
        type="single_choice",
        options=[
            "Vegetarian",
            "Non-Vegetarian",
            "Eggetarian",
            "Vegan",
            "Jain"
        ],
        category="taste"
    ),
    # Q19: Set 3 - Comfortable dinner budget
    QuizQuestion(
        id="dinner_budget",
        question="What's your comfortable per-person dinner budget?",
        subtitle="Helps us select the right restaurant tier.",
        highlight="dinner budget",
        type="single_choice",
        options=[
            "Under ₹500 (Budget-friendly dining)",
            "₹500 – ₹1,000 (Mid-Range comfort)",
            "₹1,000 – ₹2,000 (Premium dining & drinks)",
            "₹2,000+ (Exclusive fine dining luxury)"
        ],
        category="taste"
    ),
    # Q20: Fixed - Phone Number & OTP Verification
    QuizQuestion(
        id="phone_otp",
        question="What's your mobile number?",
        subtitle="We'll send an instant 6-digit OTP to verify your account & lock your seat.",
        highlight="mobile number",
        type="phone_otp",
        options=[],
        category="verification"
    )
]

ARCHETYPES = {
    "Stark": {
        "archetype": "Stark",
        "title": "The Charismatic Spark",
        "description": "Quick-witted, infectious energy, and effortlessly turns awkward silences into inside jokes.",
        "superpower": "Brings immediate laughter and keeps the table's energy vibrant all evening.",
        "icebreaker_style": "Witty Banter & Humor"
    },
    "Clark Kent": {
        "archetype": "Clark Kent",
        "title": "The Grounded Anchor",
        "description": "Warm, attentive, and puts everyone at ease. Makes every stranger feel genuinely heard.",
        "superpower": "Creates an emotionally safe, comfortable space where people open up effortlessly.",
        "icebreaker_style": "Attentive Listening & Warmth"
    },
    "Phoebe": {
        "archetype": "Phoebe",
        "title": "The Creative Storyteller",
        "description": "Quirky, authentic, and delightfully unexpected. Connects people through vivid tales.",
        "superpower": "Bridges completely different personalities with unforgettable, surreal stories.",
        "icebreaker_style": "Quirky Storytelling & Playfulness"
    },
    "Sherlock": {
        "archetype": "Sherlock",
        "title": "The Curious Inquirer",
        "description": "Thoughtful, sharp, and genuinely fascinated by what makes people tick.",
        "superpower": "Asks the exact question that ignites someone's deepest passion.",
        "icebreaker_style": "Deep & Meaningful Questions"
    },
    "Indiana": {
        "archetype": "Indiana",
        "title": "The Bold Explorer",
        "description": "Adventurous, open-minded, and thrives when stepping outside conventional boundaries.",
        "superpower": "Inspires tablemates to share their wildest adventures and try new things.",
        "icebreaker_style": "Adventure & Spontaneity"
    }
}

def calculate_archetype(answers: Dict[str, Any]) -> Dict[str, str]:
    # Analyze answers from across the questions
    scores = {"Stark": 0, "Clark Kent": 0, "Phoebe": 0, "Sherlock": 0, "Indiana": 0}
    
    # 1. Approach & Style
    q7 = str(answers.get("approach_strangers", ""))
    if "joke" in q7.lower(): scores["Stark"] += 3
    elif "smile" in q7.lower(): scores["Clark Kent"] += 2
    elif "observe" in q7.lower(): scores["Sherlock"] += 2
    
    q8 = str(answers.get("conversation_style", ""))
    if "banter" in q8.lower(): scores["Stark"] += 3
    elif "deep" in q8.lower(): scores["Clark Kent"] += 3
    elif "rabbit" in q8.lower(): scores["Phoebe"] += 3
    elif "curious" in q8.lower(): scores["Sherlock"] += 3

    # 2. Group Role
    q9 = str(answers.get("group_role", ""))
    if "spark" in q9.lower(): scores["Stark"] += 4
    elif "anchor" in q9.lower(): scores["Clark Kent"] += 4
    elif "storyteller" in q9.lower(): scores["Phoebe"] += 4
    elif "inquirer" in q9.lower(): scores["Sherlock"] += 4

    # 3. Topic & Era
    q13 = str(answers.get("favorite_topic", ""))
    if "travel" in q13.lower(): scores["Indiana"] += 3
    elif "cinema" in q13.lower() or "pop" in q13.lower(): scores["Phoebe"] += 2
    elif "ideas" in q13.lower(): scores["Sherlock"] += 2
    
    q12 = str(answers.get("spontaneity", ""))
    if "wildly" in q12.lower(): scores["Indiana"] += 3
    elif "planner" in q12.lower(): scores["Clark Kent"] += 2

    best_arch = max(scores, key=scores.get)
    if scores[best_arch] == 0:
        best_arch = "Stark"
    return ARCHETYPES.get(best_arch, ARCHETYPES["Stark"])

@router.get("/quiz", response_model=List[QuizQuestion])
def get_quiz():
    return ONBOARDING_20_QUESTIONS

@router.post("/submit", response_model=VibeDNAResult)
def submit_quiz(data: QuizSubmit, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    result_data = calculate_archetype(data.answers)
    
    # Save personality profile
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
    
    # Also update dining preferences if provided
    dietary = str(data.answers.get("dietary_preference", "No dietary restrictions"))
    budget_raw = str(data.answers.get("dinner_budget", "Mid-Range"))
    budget_tier = "mid_range"
    if "under" in budget_raw.lower(): budget_tier = "budget"
    elif "2,000" in budget_raw.lower() or "luxury" in budget_raw.lower(): budget_tier = "premium"
    
    pref = db.query(DiningPreferences).filter(DiningPreferences.user_id == current_user.id).first()
    if pref:
        pref.dietary_requirements = dietary
        pref.budget_tier = budget_tier
    else:
        pref = DiningPreferences(
            user_id=current_user.id,
            budget_tier=budget_tier,
            dietary_requirements=dietary
        )
        db.add(pref)

    db.commit()
    return VibeDNAResult(**result_data)
