from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.schemas import Job, PreferenceSignal, SearchConfig

router = APIRouter()


def job_to_dict(job: Job) -> dict:
    return {
        "id": job.id,
        "platform": job.platform,
        "external_url": job.external_url,
        "title": job.title,
        "company": job.company,
        "location": job.location,
        "salary_range": job.salary_range,
        "match_score": job.match_score,
        "status": job.status,
        "scraped_at": job.scraped_at.isoformat() if job.scraped_at else None,
    }


@router.get("/")
def list_jobs(status: str = "new", db: Session = Depends(get_db)):
    """List jobs filtered by status."""
    jobs = db.query(Job).filter(Job.status == status).order_by(
        Job.match_score.desc().nullslast()
    ).all()
    return {"jobs": [job_to_dict(j) for j in jobs]}


@router.get("/{job_id}")
def get_job(job_id: int, db: Session = Depends(get_db)):
    """Get a single job with full description."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    result = job_to_dict(job)
    result["description"] = job.description
    return result


@router.post("/search")
def trigger_search(db: Session = Depends(get_db)):
    """Trigger scraping + matching pipeline."""
    # TODO Phase 3: call scraper agent, then matcher agent
    # For now, return the current config so frontend knows what was requested
    config = db.query(SearchConfig).first()
    return {
        "message": "Search triggered",
        "jobs_found": 0,
        "platforms": config.platforms if config else [],
    }


@router.post("/{job_id}/select")
def select_job(job_id: int, profile_id: int = 1, db: Session = Depends(get_db)):
    """Mark a job as selected for application."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    job.status = "selected"
    signal = PreferenceSignal(
        resume_profile_id=profile_id,
        job_id=job_id,
        action="selected",
    )
    db.add(signal)
    db.commit()
    return {"job_id": job_id, "status": "selected"}


@router.post("/{job_id}/reject")
def reject_job(job_id: int, profile_id: int = 1, db: Session = Depends(get_db)):
    """Mark a job as rejected."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    job.status = "rejected"
    signal = PreferenceSignal(
        resume_profile_id=profile_id,
        job_id=job_id,
        action="rejected",
    )
    db.add(signal)
    db.commit()
    return {"job_id": job_id, "status": "rejected"}
