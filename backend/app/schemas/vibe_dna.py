from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class QuizQuestion(BaseModel):
    id: str
    question: str
    highlight: str
    options: List[str]

class QuizSubmit(BaseModel):
    answers: Dict[str, str]  # question_id: selected_option

class VibeDNAResult(BaseModel):
    archetype: str
    title: str
    description: str
    superpower: str
    icebreaker_style: str
