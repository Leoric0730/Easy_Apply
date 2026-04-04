from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from models.schemas import Application, Job

router = APIRouter()


class FillRequest(BaseModel):
    job_ids: list[int]
    profile_id: int


@router.get("/")
def list_applications(status: str = None, db: Session = Depends(get_db)):
    """List applications, optionally filtered by status."""
    query = db.query(Application).join(Job)
    if status:
        query = query.filter(Application.status == status)
    apps = query.order_by(Application.created_at.desc()).all()

    return {
        "applications": [
            {
                "id": a.id,
                "job_id": a.job_id,
                "job_title": a.job.title,
                "company": a.job.company,
                "platform": a.job.platform,
                "profile_label": a.resume_profile.label,
                "status": a.status,
                "browser_url": None,  # TODO Phase 6: Playwright session URL
                "applied_at": a.applied_at.isoformat() if a.applied_at else None,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in apps
        ]
    }


@router.post("/fill")
def fill_applications(req: FillRequest, db: Session = Depends(get_db)):
    """Create application records for selected jobs."""
    created = []
    for job_id in req.job_ids:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            continue
        app = Application(
            job_id=job_id,
            resume_profile_id=req.profile_id,
            status="filling",
        )
        db.add(app)
        job.status = "applied"
        created.append(job_id)

    db.commit()
    # TODO Phase 6: trigger Playwright filler agent for each application
    return {"message": f"Created {len(created)} applications", "job_ids": created}


@router.get("/{app_id}/browser-link")
def get_browser_link(app_id: int, db: Session = Depends(get_db)):
    """Get live Playwright browser session link."""
    app = db.query(Application).filter(Application.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    # TODO Phase 6: return actual Playwright CDP URL
    return {
        "app_id": app_id,
        "status": app.status,
        "browser_url": None,
    }
