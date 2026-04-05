import urllib.parse
from agents.scraper.base import BaseScraper, ScrapedJob


class LinkedInScraper(BaseScraper):
    """Scraper for LinkedIn job listings.

    Uses LinkedIn's public job search page (no login required).
    LinkedIn's public search at linkedin.com/jobs/search returns results
    without authentication, though with limited detail.
    """

    BASE_URL = "https://www.linkedin.com/jobs/search"

    @property
    def platform_name(self) -> str:
        return "linkedin"

    async def search(self, keywords: list[str], location: str = "") -> list[ScrapedJob]:
        """Search LinkedIn for jobs matching keywords.

        Uses the public job search URL which doesn't require login.
        Extracts job cards from the search results page.
        """
        await self.start_browser()
        jobs = []

        try:
            query = " ".join(keywords)
            params = {"keywords": query}
            if location:
                params["location"] = location

            url = f"{self.BASE_URL}?{urllib.parse.urlencode(params)}"
            await self._page.goto(url, wait_until="networkidle", timeout=30000)

            # Wait for job cards to load
            await self._page.wait_for_timeout(2000)

            # Scroll to load more results
            await self.scroll_to_load(pause=1.5, max_scrolls=3)

            # Extract job cards
            # LinkedIn public search uses <ul class="jobs-search__results-list">
            cards = await self._page.query_selector_all(
                "div.base-card, li.result-card, div.job-search-card"
            )

            for card in cards:
                try:
                    job = await self._parse_card(card)
                    if job:
                        jobs.append(job)
                except Exception:
                    continue

        finally:
            await self.close_browser()

        return jobs

    async def _parse_card(self, card) -> ScrapedJob | None:
        """Parse a single LinkedIn job card element."""

        # Title
        title_el = await card.query_selector(
            "h3.base-search-card__title, "
            "h3.result-card__title, "
            "span.sr-only"
        )
        title = (await title_el.inner_text()).strip() if title_el else None
        if not title:
            return None

        # Company
        company_el = await card.query_selector(
            "h4.base-search-card__subtitle, "
            "a.result-card__subtitle-link, "
            "h4.result-card__subtitle"
        )
        company = (await company_el.inner_text()).strip() if company_el else "Unknown"

        # Location
        location_el = await card.query_selector(
            "span.job-search-card__location, "
            "span.result-card__meta"
        )
        location = (await location_el.inner_text()).strip() if location_el else ""

        # URL
        link_el = await card.query_selector("a.base-card__full-link, a.result-card__full-link")
        url = ""
        if link_el:
            url = await link_el.get_attribute("href") or ""
            # Clean tracking params
            url = url.split("?")[0] if url else ""

        # Description (LinkedIn cards show limited text; full JD requires clicking in)
        desc_el = await card.query_selector("p.base-search-card__metadata, div.base-search-card__metadata")
        description = (await desc_el.inner_text()).strip() if desc_el else ""

        return ScrapedJob(
            platform="linkedin",
            title=title,
            company=company,
            location=location,
            description=description,
            external_url=url,
        )

    async def fetch_full_description(self, job_url: str) -> str:
        """Navigate to a job page and extract the full description.

        Call this after initial scraping to get complete JD text
        for better embedding quality.
        """
        await self.start_browser()
        try:
            await self._page.goto(job_url, wait_until="networkidle", timeout=30000)
            await self._page.wait_for_timeout(2000)

            desc_el = await self._page.query_selector(
                "div.show-more-less-html__markup, "
                "div.description__text, "
                "section.description"
            )
            if desc_el:
                return (await desc_el.inner_text()).strip()
            return ""
        finally:
            await self.close_browser()
