from fastapi import APIRouter
from app.api.endpoints import auth, vibe_dna, preferences, slots, reveal

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(vibe_dna.router, prefix="/vibe-dna", tags=["vibe-dna"])
api_router.include_router(preferences.router, prefix="/preferences", tags=["preferences"])
api_router.include_router(slots.router, prefix="/slots", tags=["slots"])
api_router.include_router(reveal.router, prefix="/reveal", tags=["reveal"])
