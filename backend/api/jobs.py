from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db

router = APIRouter()


@router.get("/")
def list_jobs(status: str = "new", db: Session = Depends(get_db)):
    """List jobs filtered by status."""
    # TODO: implement with actual DB query
    return {"jobs": [], "status": status}


@router.post("/search")
def trigger_search(db: Session = Depends(get_db)):
    """Trigger scraping + matching pipeline."""
    # TODO: call scraper agent, then matcher agent
    return {"message": "Search triggered", "jobs_found": 0}


@router.post("/{job_id}/select")
def select_job(job_id: int, db: Session = Depends(get_db)):
    """Mark a job as selected for application."""
    # TODO: update job status, create preference signal
    return {"job_id": job_id, "status": "selected"}


@router.post("/{job_id}/reject")
def reject_job(job_id: int, db: Session = Depends(get_db)):
    """Mark a job as rejected."""
    # TODO: update job status, create preference signal
    return {"job_id": job_id, "status": "rejected"}
