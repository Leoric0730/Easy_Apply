import os
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.schemas import User, ResumeProfile
from services.resume_parser import parse_resume

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

router = APIRouter()


def get_or_create_user(db: Session) -> User:
    """Get the single user, or create one if none exists."""
    user = db.query(User).first()
    if not user:
        user = User(name="Default User", email="user@example.com")
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


@router.get("/")
def list_profiles(db: Session = Depends(get_db)):
    """List all resume profiles."""
    profiles = db.query(ResumeProfile).all()
    return {
        "profiles": [
            {
                "id": p.id,
                "label": p.label,
                "resume_file_path": p.resume_file_path,
                "target_keywords": p.target_keywords,
                "has_embedding": p.embedding is not None,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in profiles
        ]
    }


@router.post("/")
def create_profile(
    label: str = Form(...),
    target_keywords: str = Form(""),
    db: Session = Depends(get_db),
):
    """Create a new resume profile."""
    user = get_or_create_user(db)
    keywords = [k.strip() for k in target_keywords.split(",") if k.strip()]
    profile = ResumeProfile(
        user_id=user.id,
        label=label,
        target_keywords=keywords,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return {"id": profile.id, "label": profile.label}


@router.post("/{profile_id}/upload-resume")
async def upload_resume(
    profile_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload a resume PDF for a profile."""
    profile = db.query(ResumeProfile).filter(ResumeProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    file_path = os.path.join(UPLOAD_DIR, f"resume_{profile_id}_{file.filename}")
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    profile.resume_file_path = file_path

    # Parse resume into structured sections
    parsed = parse_resume(file_path)
    profile.parsed_content = parsed

    # Generate embedding from resume text (lazy import to avoid startup crash)
    raw_text = parsed.get("raw_text", "")
    if raw_text:
        try:
            from services.embedding import embed_text
            vec = embed_text(raw_text)
            profile.embedding = vec.tobytes()
        except ImportError:
            pass  # embedding dependencies not available locally

    db.commit()

    return {
        "profile_id": profile_id,
        "filename": file.filename,
        "sections_found": list(parsed.get("sections", {}).keys()),
        "has_embedding": profile.embedding is not None,
    }


@router.delete("/{profile_id}")
def delete_profile(profile_id: int, db: Session = Depends(get_db)):
    """Delete a resume profile."""
    profile = db.query(ResumeProfile).filter(ResumeProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    db.delete(profile)
    db.commit()
    return {"message": f"Profile {profile_id} deleted"}
