import os
from typing import List
from datetime import datetime
from backend.models import JobListing, SearchConfig
from backend.adapters.base import BaseAdapter

class JoobleAdapter(BaseAdapter):
    def __init__(self):
        super().__init__("Jooble")
        self.api_key = os.getenv("JOOBLE_API_KEY")
        self.url = f"https://jooble.org/api/combined/{self.api_key}" if self.api_key else ""

    async def search(self, config: SearchConfig) -> List[JobListing]:
        if not self.api_key:
            print(f"Jooble API key missing, skipping {self.name}")
            return []

        payload = {
            "keywords": config.keywords,
            "location": config.location if config.location else ""
        }

        try:
            data = await self._post(self.url, json_body=payload)
            jobs = data.get("jobs", [])
            
            listings = []
            for job in jobs:
                # Jooble date (needs careful parsing)
                try:
                    posted_at = datetime.fromisoformat(job.get("updated", "").replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    posted_at = datetime.now()

                listing = JobListing(
                    title=job.get("title"),
                    company=job.get("company"),
                    location=job.get("location"),
                    url=job.get("link"),
                    source=self.name,
                    posted_at=posted_at,
                    salary=job.get("salary"),
                    is_remote="remote" in job.get("location", "").lower() or 
                              "remote" in job.get("title", "").lower()
                )
                listings.append(listing)
            return listings
        except Exception as e:
            print(f"Error fetching from {self.name}: {e}")
            return []
