import os
from typing import List
from datetime import datetime, timezone
from backend.models import JobListing, SearchConfig
from backend.adapters.base import BaseAdapter


class JoobleAdapter(BaseAdapter):
    def __init__(self):
        super().__init__("Jooble")
        self.api_key = os.getenv("JOOBLE_API_KEY")

    async def search(self, config: SearchConfig) -> List[JobListing]:
        if not self.api_key:
            print(f"Jooble API key missing, skipping {self.name}")
            return []

        # Jooble returns up to 20 results per request; query each phrase separately
        # to maximize coverage for multi-phrase keyword lists.
        keyword_phrases = [kw.strip() for kw in config.keywords.split(",") if kw.strip()]
        url = f"https://jooble.org/api/{self.api_key}"

        seen_urls: set = set()
        all_listings: List[JobListing] = []

        for phrase in keyword_phrases:
            payload = {
                "keywords": phrase,
                "location": config.location if config.location else "",
                "resultonpage": 20,
            }
            try:
                data = await self._post(url, json_body=payload)
                jobs = data.get("jobs", [])
                for job in jobs:
                    link = job.get("link", "")
                    if not link or link in seen_urls:
                        continue
                    seen_urls.add(link)
                    try:
                        posted_at = datetime.fromisoformat(
                            job.get("updated", "").replace("Z", "+00:00")
                        )
                    except (ValueError, TypeError):
                        posted_at = datetime.now(timezone.utc)

                    all_listings.append(JobListing(
                        title=job.get("title", ""),
                        company=job.get("company", ""),
                        location=job.get("location", ""),
                        url=link,
                        source=self.name,
                        posted_at=posted_at,
                        salary=job.get("salary"),
                        is_remote=(
                            "remote" in job.get("location", "").lower() or
                            "remote" in job.get("title", "").lower()
                        ),
                        description=job.get("snippet", ""),
                    ))
            except Exception as e:
                print(f"Error fetching from {self.name} (phrase='{phrase}'): {e}")

        return all_listings
