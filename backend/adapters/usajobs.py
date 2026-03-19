import os
from typing import List
from datetime import datetime
from backend.models import JobListing, SearchConfig
from backend.adapters.base import BaseAdapter

class USAJobsAdapter(BaseAdapter):
    def __init__(self):
        super().__init__("USAJobs")
        self.api_key = os.getenv("USAJOBS_API_KEY")
        self.email = os.getenv("USAJOBS_EMAIL")
        self.url = "https://data.usajobs.gov/api/search"

    async def search(self, config: SearchConfig) -> List[JobListing]:
        if not self.api_key or not self.email:
            print(f"USAJobs credentials missing, skipping {self.name}")
            return []

        headers = {
            "Host": "data.usajobs.gov",
            "User-Agent": self.email,
            "Authorization-Key": self.api_key
        }

        params = {
            "Keyword": config.keywords,
            "LocationName": config.location if config.location else ""
        }

        try:
            data = await self._get(self.url, params=params, headers=headers)
            items = data.get("SearchResult", {}).get("SearchResultItems", [])
            
            listings = []
            for item in items:
                desc = item.get("MatchedObjectDescriptor", {})
                
                # USAJobs date
                try:
                    posted_at = datetime.fromisoformat(desc.get("PublicationStartDate", "").replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    posted_at = datetime.now()

                location = desc.get("PositionLocation", [{}])[0].get("LocationName", "Remote")
                
                listing = JobListing(
                    title=desc.get("PositionTitle"),
                    company=desc.get("OrganizationName"),
                    location=location,
                    url=desc.get("PositionURI"),
                    source=self.name,
                    posted_at=posted_at,
                    salary=desc.get("PositionRemuneration", [{}])[0].get("MinimumRange"),
                    is_remote="remote" in location.lower() or 
                              "remote" in desc.get("PositionTitle", "").lower()
                )
                listings.append(listing)
            return listings
        except Exception as e:
            print(f"Error fetching from {self.name}: {e}")
            return []
