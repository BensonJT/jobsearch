import asyncio
from datetime import datetime, timezone
from typing import List
from backend.models import JobListing, SearchConfig
from backend.adapters.base import BaseAdapter

# Fetch unfiltered pages — The Muse category names are inconsistent.
# Apply keyword matching client-side for reliability.
PAGES_TO_FETCH = 10  # 20 results/page = up to 200 candidates before keyword filter


class TheMuseAdapter(BaseAdapter):
    def __init__(self):
        super().__init__("TheMuse")
        self.base_url = "https://www.themuse.com/api/public/jobs"

    async def search(self, config: SearchConfig) -> List[JobListing]:
        keyword_phrases = [kw.strip().lower() for kw in config.keywords.split(",") if kw.strip()]

        tasks = [self._fetch_page(page) for page in range(PAGES_TO_FETCH)]
        pages = await asyncio.gather(*tasks, return_exceptions=True)

        seen_urls: set = set()
        listings: List[JobListing] = []

        for page_result in pages:
            if not isinstance(page_result, list):
                continue
            for item in page_result:
                url = item.get("refs", {}).get("landing_page", "")
                if not url or url in seen_urls:
                    continue

                title = item.get("name", "")
                description = item.get("contents", "")
                text_to_scan = (title + " " + description).lower()

                if not any(phrase in text_to_scan for phrase in keyword_phrases):
                    continue

                raw_locations = item.get("locations", [])
                location_str = ", ".join(loc.get("name", "") for loc in raw_locations) or "Unknown"
                is_remote = any(
                    "remote" in loc.get("name", "").lower()
                    or "flexible" in loc.get("name", "").lower()
                    for loc in raw_locations
                )

                if config.location and config.location.lower() == "remote" and not is_remote:
                    continue

                try:
                    posted_at = datetime.fromisoformat(
                        item.get("publication_date", "").replace("Z", "+00:00")
                    )
                except (ValueError, TypeError):
                    posted_at = datetime.now(timezone.utc)

                seen_urls.add(url)
                listings.append(JobListing(
                    title=title,
                    company=item.get("company", {}).get("name", "Unknown"),
                    location=location_str,
                    url=url,
                    source=self.name,
                    posted_at=posted_at,
                    description=description[:500],
                    is_remote=is_remote,
                ))

        return listings

    async def _fetch_page(self, page: int) -> List[dict]:
        try:
            data = await self._get(self.base_url, params={
                "page": page,
                "descending": "true",
            })
            return data.get("results", [])
        except Exception as e:
            print(f"TheMuse error (page {page}): {e}")
            return []
