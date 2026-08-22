from typing import Dict
from fastapi import APIRouter

router = APIRouter()


@router.get("/health", response_model=Dict[str, str], tags=["Health"])
def health_check() -> Dict[str, str]:
    """Health check endpoint to verify system and API responsiveness."""
    return {"status": "ok"}
