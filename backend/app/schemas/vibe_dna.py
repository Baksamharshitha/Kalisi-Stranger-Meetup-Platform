from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class QuizQuestion(BaseModel):
    id: str
    question: str
    subtitle: Optional[str] = ""
    highlight: Optional[str] = ""
    type: str = "single_choice"  # text, age, single_choice, scale, phone_otp
    options: List[str] = []
    category: str = "vibe"

class QuizSubmit(BaseModel):
    answers: Dict[str, Any]

class VibeDNAResult(BaseModel):
    archetype: str
    title: str
    description: str
    superpower: str
    icebreaker_style: str
