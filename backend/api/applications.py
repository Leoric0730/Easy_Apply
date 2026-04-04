from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db

router = APIRouter()


@router.get("/")
def list_applications(status: str = None, db: Session = Depends(get_db)):
    """List applications, optionally filtered by status."""
    # TODO: implement with actual DB query
    return {"applications": [], "status": status}


@router.post("/fill")
def fill_applications(job_ids: list[int], profile_id: int, db: Session = Depends(get_db)):
    """Trigger filler agent for selected jobs."""
    # TODO: launch Playwright sessions, fill forms
    return {"message": f"Filling {len(job_ids)} applications", "job_ids": job_ids}


@router.get("/{app_id}/browser-link")
def get_browser_link(app_id: int, db: Session = Depends(get_db)):
    """Get live Playwright browser session link."""
    # TODO: return browser remote debugging URL
    return {"app_id": app_id, "browser_url": None}
