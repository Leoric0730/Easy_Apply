from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from database import get_db

router = APIRouter()


@router.get("/")
def list_profiles(db: Session = Depends(get_db)):
    """List all resume profiles."""
    # TODO: query resume_profiles table
    return {"profiles": []}


@router.post("/")
def create_profile(label: str = Form(...), db: Session = Depends(get_db)):
    """Create a new resume profile."""
    # TODO: create profile in DB
    return {"message": f"Profile '{label}' created"}


@router.post("/{profile_id}/upload-resume")
def upload_resume(profile_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload and parse a resume PDF for a profile."""
    # TODO: save file, parse to JSON, generate embedding
    return {"profile_id": profile_id, "filename": file.filename}
