from abc import ABC, abstractmethod
from dataclasses import dataclass
from playwright.async_api import async_playwright, Browser, Page


@dataclass
class ScrapedJob:
    """Raw job data extracted from a platform."""
    platform: str
    title: str
    company: str
    location: str
    description: str
    external_url: str
    salary_range: str | None = None


class BaseScraper(ABC):
    """Base class for all platform scrapers.

    Each platform scraper implements:
    - platform_name: identifier string
    - search(): navigates to the platform, searches, and returns ScrapedJob list
    """

    def __init__(self):
        self._browser: Browser | None = None
        self._page: Page | None = None

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Platform identifier (e.g. 'linkedin', 'boss_zhipin')."""
        ...

    @abstractmethod
    async def search(self, keywords: list[str], location: str = "") -> list[ScrapedJob]:
        """Search for jobs on this platform.

        Args:
            keywords: Search terms (e.g. ["machine learning engineer"])
            location: Optional location filter

        Returns:
            List of ScrapedJob objects
        """
        ...

    async def start_browser(self, headless: bool = True):
        """Launch a Playwright browser."""
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=headless)
        self._page = await self._browser.new_page()
        # Set a realistic viewport and user agent
        await self._page.set_viewport_size({"width": 1280, "height": 800})

    async def close_browser(self):
        """Clean up browser resources."""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        self._browser = None
        self._page = None

    async def safe_get_text(self, selector: str, default: str = "") -> str:
        """Safely extract text from an element, returning default if not found."""
        try:
            el = await self._page.query_selector(selector)
            if el:
                return (await el.inner_text()).strip()
        except Exception:
            pass
        return default

    async def safe_get_attribute(self, selector: str, attr: str, default: str = "") -> str:
        """Safely extract an attribute from an element."""
        try:
            el = await self._page.query_selector(selector)
            if el:
                val = await el.get_attribute(attr)
                return val.strip() if val else default
        except Exception:
            pass
        return default

    async def scroll_to_load(self, pause: float = 1.5, max_scrolls: int = 5):
        """Scroll down to trigger lazy-loaded content."""
        for _ in range(max_scrolls):
            await self._page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await self._page.wait_for_timeout(int(pause * 1000))
