import numpy as np
from sqlalchemy.orm import Session
from models.schemas import Job, ResumeProfile, PreferenceSignal


def rank_jobs(
    db: Session,
    profile_id: int,
    job_ids: list[int] | None = None,
) -> list[dict]:
    """Rank jobs by combining stored match_score + preference signals.

    Args:
        db: Database session
        profile_id: Which resume profile to match against
        job_ids: Optional list of job IDs to rank. If None, ranks all 'new' jobs.

    Returns:
        List of {job_id, score, similarity, preference_boost} sorted by score desc.
    """
    # Get jobs to rank
    if job_ids:
        jobs = db.query(Job).filter(Job.id.in_(job_ids)).all()
    else:
        jobs = db.query(Job).filter(Job.status == "new").all()

    if not jobs:
        return []

    # Compute preference boosts from accept/reject history
    preference_boosts = _compute_preference_boosts(db, profile_id, jobs)

    # Combine: stored match_score (similarity) + preference boost
    SIMILARITY_WEIGHT = 0.7
    PREFERENCE_WEIGHT = 0.3

    ranked = []
    for job in jobs:
        sim = job.match_score or 0.0
        pref = preference_boosts.get(job.id, 0.0)
        combined = sim * SIMILARITY_WEIGHT + pref * PREFERENCE_WEIGHT

        ranked.append({
            "job_id": job.id,
            "score": round(combined, 4),
            "similarity": round(sim, 4),
            "preference_boost": round(pref, 4),
        })

    ranked.sort(key=lambda x: x["score"], reverse=True)
    return ranked


def _compute_preference_boosts(
    db: Session,
    profile_id: int,
    jobs: list[Job],
) -> dict[int, float]:
    """Compute preference boost for each job based on past accept/reject patterns.

    Learns from the user's history:
    - Companies the user tends to select → positive boost
    - Companies the user tends to reject → negative boost
    - Keywords that appear in selected jobs → positive boost

    Returns dict of {job_id: boost_score} in range [-1.0, 1.0].
    """
    # Get all past signals for this profile
    signals = (
        db.query(PreferenceSignal)
        .filter(PreferenceSignal.resume_profile_id == profile_id)
        .all()
    )

    if not signals:
        return {job.id: 0.0 for job in jobs}

    # Build company preference map
    company_scores = {}
    for signal in signals:
        signal_job = db.query(Job).filter(Job.id == signal.job_id).first()
        if not signal_job:
            continue

        company = signal_job.company.lower()
        if company not in company_scores:
            company_scores[company] = {"selected": 0, "rejected": 0}

        if signal.action == "selected":
            company_scores[company]["selected"] += 1
        elif signal.action == "rejected":
            company_scores[company]["rejected"] += 1

    # Build keyword preference map from selected job titles/descriptions
    keyword_scores = {}
    for signal in signals:
        if signal.action != "selected":
            continue
        signal_job = db.query(Job).filter(Job.id == signal.job_id).first()
        if not signal_job:
            continue

        # Extract words from title
        words = signal_job.title.lower().split()
        for word in words:
            if len(word) > 2:  # skip short words
                keyword_scores[word] = keyword_scores.get(word, 0) + 1

    # Compute boost for each candidate job
    boosts = {}
    for job in jobs:
        boost = 0.0

        # Company preference
        company = job.company.lower()
        if company in company_scores:
            cs = company_scores[company]
            total = cs["selected"] + cs["rejected"]
            if total > 0:
                # Range: -1.0 (all rejected) to +1.0 (all selected)
                boost += (cs["selected"] - cs["rejected"]) / total * 0.5

        # Keyword overlap with previously selected job titles
        if keyword_scores:
            title_words = set(job.title.lower().split())
            max_kw_score = max(keyword_scores.values())
            overlap_score = sum(
                keyword_scores.get(w, 0) / max_kw_score
                for w in title_words
                if w in keyword_scores
            )
            # Normalize by number of title words to avoid bias toward long titles
            if title_words:
                boost += min(overlap_score / len(title_words), 0.5)

        boosts[job.id] = max(-1.0, min(1.0, boost))  # clamp to [-1, 1]

    return boosts


def embed_and_score_jobs(db: Session, profile_id: int, jobs: list[Job]):
    """Embed new jobs and compute match scores.

    Called after scraping to:
    1. Generate embeddings for jobs that don't have one
    2. Compute and store match_score (cosine similarity) for each job
    """
    try:
        from services.embedding import embed_text
    except ImportError:
        return

    profile = db.query(ResumeProfile).filter(ResumeProfile.id == profile_id).first()
    if not profile or not profile.embedding:
        return

    resume_vec = np.frombuffer(profile.embedding, dtype=np.float32)

    for job in jobs:
        # Generate embedding if missing
        if not job.embedding and job.description:
            vec = embed_text(job.description)
            job.embedding = vec.tobytes()

        # Compute match score (pure cosine similarity)
        if job.embedding:
            job_vec = np.frombuffer(job.embedding, dtype=np.float32)
            job.match_score = float(np.dot(resume_vec, job_vec))

    db.commit()
