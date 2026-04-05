from datetime import datetime
from sqlalchemy.orm import Session
from agents.scraper.base import BaseScraper, ScrapedJob
from agents.scraper.linkedin import LinkedInScraper
from agents.scraper.boss_zhipin import BossZhipinScraper
from models.schemas import Job

# Registry: platform name → scraper class
SCRAPERS: dict[str, type[BaseScraper]] = {
    "linkedin": LinkedInScraper,
    "boss_zhipin": BossZhipinScraper,
}


def is_duplicate(db: Session, job: ScrapedJob) -> bool:
    """Check if a job already exists in the database.

    Matches on company + title + location (case-insensitive).
    """
    existing = (
        db.query(Job)
        .filter(
            Job.company.ilike(job.company),
            Job.title.ilike(job.title),
            Job.location.ilike(job.location) if job.location else True,
        )
        .first()
    )
    return existing is not None


async def run_scraper(
    platforms: list[str],
    keywords: list[str],
    location: str,
    db: Session,
) -> list[Job]:
    """Run scrapers for the specified platforms and store results.

    Args:
        platforms: List of platform names (e.g. ["linkedin", "boss_zhipin"])
        keywords: Search keywords
        location: Location filter
        db: Database session

    Returns:
        List of newly created Job records
    """
    new_jobs = []

    for platform in platforms:
        scraper_cls = SCRAPERS.get(platform)
        if not scraper_cls:
            continue

        scraper = scraper_cls()
        try:
            scraped = await scraper.search(keywords, location)
        except Exception as e:
            print(f"[Scraper] {platform} failed: {e}")
            continue

        for s in scraped:
            if is_duplicate(db, s):
                continue

            job = Job(
                platform=s.platform,
                title=s.title,
                company=s.company,
                location=s.location,
                description=s.description,
                external_url=s.external_url,
                salary_range=s.salary_range,
                status="new",
                scraped_at=datetime.utcnow(),
            )
            db.add(job)
            new_jobs.append(job)

    db.commit()

    # Refresh to get auto-generated IDs
    for job in new_jobs:
        db.refresh(job)

    return new_jobs
