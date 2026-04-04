from datetime import time
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from models.schemas import SearchConfig, User


router = APIRouter()


class ConfigUpdate(BaseModel):
    platforms: list[str] | None = None
    resume_profile_id: int | None = None
    filters: dict | None = None
    auto_search_enabled: bool | None = None
    auto_search_time: str | None = None  # "HH:MM" format


def get_or_create_config(db: Session) -> SearchConfig:
    """Get the single search config, or create a default one."""
    config = db.query(SearchConfig).first()
    if not config:
        user = db.query(User).first()
        if not user:
            user = User(name="Default User", email="user@example.com")
            db.add(user)
            db.commit()
            db.refresh(user)
        config = SearchConfig(
            user_id=user.id,
            platforms=["linkedin"],
            filters={},
            auto_search_enabled=False,
            auto_search_time=time(9, 0),
        )
        db.add(config)
        db.commit()
        db.refresh(config)
    return config


@router.get("/")
def get_search_config(db: Session = Depends(get_db)):
    """Get current search configuration."""
    config = get_or_create_config(db)
    return {
        "platforms": config.platforms,
        "resume_profile_id": config.resume_profile_id,
        "filters": config.filters,
        "auto_search_enabled": config.auto_search_enabled,
        "auto_search_time": config.auto_search_time.strftime("%H:%M") if config.auto_search_time else "09:00",
    }


@router.put("/")
def update_search_config(update: ConfigUpdate, db: Session = Depends(get_db)):
    """Update search configuration."""
    config = get_or_create_config(db)

    if update.platforms is not None:
        config.platforms = update.platforms
    if update.resume_profile_id is not None:
        config.resume_profile_id = update.resume_profile_id
    if update.filters is not None:
        config.filters = update.filters
    if update.auto_search_enabled is not None:
        config.auto_search_enabled = update.auto_search_enabled
    if update.auto_search_time is not None:
        h, m = update.auto_search_time.split(":")
        config.auto_search_time = time(int(h), int(m))

    db.commit()
    return {"message": "Config updated"}
