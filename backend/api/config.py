from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db

router = APIRouter()


@router.get("/")
def get_search_config(db: Session = Depends(get_db)):
    """Get current search configuration."""
    # TODO: query search_configs table
    return {
        "platforms": ["linkedin"],
        "resume_profile_id": None,
        "filters": {},
        "auto_search_enabled": False,
        "auto_search_time": "09:00"
    }


@router.put("/")
def update_search_config(
    platforms: list[str] = None,
    resume_profile_id: int = None,
    auto_search_enabled: bool = None,
    db: Session = Depends(get_db)
):
    """Update search configuration."""
    # TODO: update search_configs table
    return {"message": "Config updated"}
