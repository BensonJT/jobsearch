import os
from typing import List
from datetime import datetime
from backend.models import JobListing, SearchConfig
from backend.adapters.base import BaseAdapter

class AdzunaAdapter(BaseAdapter):
    def __init__(self):
        super().__init__("Adzuna")
        self.app_id = os.getenv("ADZUNA_APP_ID")
        self.app_key = os.getenv("ADZUNA_APP_KEY")
        self.country = os.getenv("SEARCH_COUNTRY", "us")
        self.base_url = f"https://api.adzuna.com/v1/api/jobs/{self.country}/search"

    async def search(self, config: SearchConfig) -> List[JobListing]:
        if not self.app_id or not self.app_key:
            print(f"Adzuna credentials missing, skipping {self.name}")
            return []

        params = {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "what": config.keywords,
            "where": config.location if config.location else "",
            "results_per_page": 50,
            "content-type": "application/json"
        }

        try:
            data = await self._get(f"{self.base_url}/1", params=params)
            results = data.get("results", [])
            
            listings = []
            for result in results:
                # Parse Adzuna date (typically ISO 8601)
                try:
                    posted_at = datetime.fromisoformat(result.get("created", "").replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    posted_at = datetime.now()

                listing = JobListing(
                    title=result.get("title"),
                    company=result.get("company", {}).get("display_name", "Unknown"),
                    location=result.get("location", {}).get("display_name", "Remote"),
                    url=result.get("redirect_url"),
                    source=self.name,
                    posted_at=posted_at,
                    salary=str(result.get("salary_min")) if result.get("salary_min") else None,
                    is_remote="remote" in result.get("location", {}).get("display_name", "").lower() or 
                              "remote" in result.get("title", "").lower(),
                    description=result.get("description")
                )
                listings.append(listing)
            return listings
        except Exception as e:
            print(f"Error fetching from {self.name}: {e}")
            return []
