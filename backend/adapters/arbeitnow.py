from typing import List
from datetime import datetime, timezone
from backend.models import JobListing, SearchConfig
from backend.adapters.base import BaseAdapter


class ArbeitnowAdapter(BaseAdapter):
    def __init__(self):
        super().__init__("Arbeitnow")
        self.url = "https://www.arbeitnow.com/api/job-board-api"

    async def search(self, config: SearchConfig) -> List[JobListing]:
        try:
            data = await self._get(self.url)
            jobs = data.get("data", [])

            # Split comma-separated keyword phrases for OR matching
            keyword_phrases = [kw.strip().lower() for kw in config.keywords.split(",") if kw.strip()]

            listings = []
            for item in jobs:
                title = item.get("title", "")
                description = item.get("description", "")
                text_to_scan = (title + " " + description).lower()

                # OR match: any keyword phrase found in title or description
                if not any(phrase in text_to_scan for phrase in keyword_phrases):
                    continue

                # Location filter
                item_location = item.get("location", "").lower()
                if config.location and config.location.lower() == "remote":
                    if "remote" not in item_location and "anywhere" not in item_location:
                        continue
                elif config.location and config.location.lower() not in item_location:
                    continue

                # Parse created_at as Unix timestamp (Arbeitnow API standard)
                raw_ts = item.get("created_at", 0)
                try:
                    posted_at = datetime.fromtimestamp(int(raw_ts), tz=timezone.utc)
                except (ValueError, TypeError, OSError):
                    posted_at = datetime.now(timezone.utc)

                listing = JobListing(
                    title=title,
                    company=item.get("company_name", "Unknown"),
                    location=item.get("location", "Remote"),
                    url=item.get("url", ""),
                    source=self.name,
                    posted_at=posted_at,
                    description=description,
                    is_remote="remote" in item_location or "anywhere" in item_location,
                )
                listings.append(listing)
            return listings
        except Exception as e:
            print(f"Error fetching from {self.name}: {e}")
            return []
