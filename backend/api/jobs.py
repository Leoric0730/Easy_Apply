from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from models.schemas import Job, PreferenceSignal, SearchConfig, ResumeProfile
from agents.scraper.manager import run_scraper
from agents.matcher import rank_jobs, embed_and_score_jobs

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


@router.post("/rank")
def rank_batch(profile_id: int, db: Session = Depends(get_db)):
    """Re-rank all 'new' jobs using embedding similarity + preference signals.

    Updates match_score in the database and returns the ranked list.
    """
    rankings = rank_jobs(db, profile_id)

    # Update match_score in DB for each job
    for r in rankings:
        job = db.query(Job).filter(Job.id == r["job_id"]).first()
        if job:
            job.match_score = r["score"]
    db.commit()

    return {"rankings": rankings, "total": len(rankings)}


@router.get("/{job_id}")
def get_job(job_id: int, db: Session = Depends(get_db)):
    """Get a single job with full description."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    result = job_to_dict(job)
    result["description"] = job.description
    return result


class SearchRequest(BaseModel):
    platforms: list[str] | None = None
    keywords: str | None = None
    location: str | None = None


@router.post("/search")
async def trigger_search(req: SearchRequest = None, db: Session = Depends(get_db)):
    """Trigger scraping + matching pipeline.

    Uses search config from DB, overridden by any fields in the request body.
    """
    config = db.query(SearchConfig).first()

    # Determine platforms: request body > config > default
    platforms = (req and req.platforms) or (config and config.platforms) or ["linkedin"]

    # Determine keywords: request body > active profile's target_keywords
    keywords = []
    if req and req.keywords:
        keywords = [k.strip() for k in req.keywords.split(",") if k.strip()]
    elif config and config.resume_profile_id:
        profile = db.query(ResumeProfile).filter(
            ResumeProfile.id == config.resume_profile_id
        ).first()
        if profile and profile.target_keywords:
            keywords = profile.target_keywords

    if not keywords:
        return {"message": "No keywords provided", "jobs_found": 0}

    location = (req and req.location) or ""

    # Sync current search params back to saved config
    # so auto-search uses the same settings next time
    if config:
        if req and req.platforms:
            config.platforms = platforms
        if req and req.location:
            config.filters = {**(config.filters or {}), "location": location}
        db.commit()

    # Run scrapers
    new_jobs = await run_scraper(platforms, keywords, location, db)

    # Embed new jobs and compute similarity scores
    profile_id = config.resume_profile_id if config else None
    if profile_id and new_jobs:
        # Step 1: embed job descriptions + compute cosine similarity
        embed_and_score_jobs(db, profile_id, new_jobs)

        # Step 2: apply preference boosts and update final match_score
        job_ids = [j.id for j in new_jobs]
        rankings = rank_jobs(db, profile_id, job_ids)
        for r in rankings:
            job = db.query(Job).filter(Job.id == r["job_id"]).first()
            if job:
                job.match_score = r["score"]
        db.commit()

    return {
        "message": f"Search complete on {', '.join(platforms)}",
        "jobs_found": len(new_jobs),
        "platforms": platforms,
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
