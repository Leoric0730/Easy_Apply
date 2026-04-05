import urllib.parse
from agents.scraper.base import BaseScraper, ScrapedJob


class BossZhipinScraper(BaseScraper):
    """Scraper for Boss直聘 (zhipin.com) job listings.

    Boss直聘 is one of China's largest recruitment platforms.
    Uses the public search page at zhipin.com/web/geek/job.
    """

    BASE_URL = "https://www.zhipin.com/web/geek/job"

    @property
    def platform_name(self) -> str:
        return "boss_zhipin"

    async def search(self, keywords: list[str], location: str = "") -> list[ScrapedJob]:
        """Search Boss直聘 for jobs matching keywords.

        Args:
            keywords: Search terms (e.g. ["大模型工程师", "AI Agent"])
            location: City name (e.g. "北京", "上海")
        """
        await self.start_browser()
        jobs = []

        try:
            query = " ".join(keywords)
            params = {"query": query, "page": "1"}
            if location:
                params["city"] = location

            url = f"{self.BASE_URL}?{urllib.parse.urlencode(params)}"
            await self._page.goto(url, wait_until="networkidle", timeout=30000)
            await self._page.wait_for_timeout(2000)

            # Scroll to load more listings
            await self.scroll_to_load(pause=1.5, max_scrolls=3)

            # Boss直聘 job cards are in <li> elements within the job list
            cards = await self._page.query_selector_all(
                "li.job-card-wrapper, "
                "div.job-card-body, "
                "div.search-job-result li"
            )

            for card in cards:
                try:
                    job = await self._parse_card(card)
                    if job:
                        jobs.append(job)
                except Exception:
                    continue

            # Try second page if first page loaded successfully
            if cards:
                jobs.extend(await self._scrape_next_page())

        finally:
            await self.close_browser()

        return jobs

    async def _parse_card(self, card) -> ScrapedJob | None:
        """Parse a single Boss直聘 job card."""

        # Job title
        title_el = await card.query_selector(
            "span.job-name, "
            "a.job-card-left .job-name, "
            "div.job-title .job-name"
        )
        title = (await title_el.inner_text()).strip() if title_el else None
        if not title:
            return None

        # Company name
        company_el = await card.query_selector(
            "h3.company-name, "
            "a.company-name, "
            "div.company-info h3"
        )
        company = (await company_el.inner_text()).strip() if company_el else "未知公司"

        # Location (Boss直聘 often combines city + district)
        location_el = await card.query_selector(
            "span.job-area, "
            "span.job-card-desc, "
            "div.job-info span.job-area"
        )
        location = (await location_el.inner_text()).strip() if location_el else ""

        # Salary
        salary_el = await card.query_selector(
            "span.salary, "
            "span.job-limit .red"
        )
        salary = (await salary_el.inner_text()).strip() if salary_el else None

        # Job URL
        link_el = await card.query_selector("a[href*='/job_detail/'], a.job-card-left")
        url = ""
        if link_el:
            href = await link_el.get_attribute("href") or ""
            if href.startswith("/"):
                url = f"https://www.zhipin.com{href}"
            else:
                url = href

        # Tags/keywords shown on card (e.g. "Python", "深度学习", "3-5年")
        tag_els = await card.query_selector_all(
            "ul.tag-list li, "
            "div.job-card-footer .tag-list li, "
            "ul.job-keyword li"
        )
        tags = []
        for tag_el in tag_els:
            text = (await tag_el.inner_text()).strip()
            if text:
                tags.append(text)

        description = " | ".join(tags) if tags else ""

        return ScrapedJob(
            platform="boss_zhipin",
            title=title,
            company=company,
            location=location,
            description=description,
            external_url=url,
            salary_range=salary,
        )

    async def _scrape_next_page(self) -> list[ScrapedJob]:
        """Try to navigate to and scrape the second page."""
        jobs = []
        try:
            next_btn = await self._page.query_selector(
                "a.next, "
                "div.options-pages a:has-text('下一页')"
            )
            if next_btn:
                await next_btn.click()
                await self._page.wait_for_timeout(2000)
                await self.scroll_to_load(pause=1.5, max_scrolls=2)

                cards = await self._page.query_selector_all(
                    "li.job-card-wrapper, "
                    "div.job-card-body, "
                    "div.search-job-result li"
                )
                for card in cards:
                    try:
                        job = await self._parse_card(card)
                        if job:
                            jobs.append(job)
                    except Exception:
                        continue
        except Exception:
            pass
        return jobs

    async def fetch_full_description(self, job_url: str) -> str:
        """Navigate to a Boss直聘 job detail page and extract full JD."""
        await self.start_browser()
        try:
            await self._page.goto(job_url, wait_until="networkidle", timeout=30000)
            await self._page.wait_for_timeout(2000)

            desc_el = await self._page.query_selector(
                "div.job-detail-section, "
                "div.job-sec-text, "
                "div.text"
            )
            if desc_el:
                return (await desc_el.inner_text()).strip()
            return ""
        finally:
            await self.close_browser()
