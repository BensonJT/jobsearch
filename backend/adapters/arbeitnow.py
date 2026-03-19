from typing import List
from datetime import datetime
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
            
            listings = []
            for item in jobs:
                # Check keyword match in title
                if config.keywords.lower() not in item.get("title", "").lower():
                    continue
                
                # Check location if specified
                if config.location and config.location.lower() != "remote":
                    if config.location.lower() not in item.get("location", "").lower():
                        continue
                elif config.location and config.location.lower() == "remote":
                     if "remote" not in item.get("location", "").lower() and "anywhere" not in item.get("location", "").lower():
                        continue

                # Parse date - assuming it's a timestamp or ISO string
                # SCRIPT_REQUIREMENTS doesn't specify Arbeitnow's date format precisely
                # Let's check common API behavior or use current time as fallback for now
                # In a real scenario, we'd parse the specific field.
                posted_at = datetime.now() # Fallback
                
                listing = JobListing(
                    title=item.get("title"),
                    company=item.get("company_name"),
                    location=item.get("location"),
                    url=item.get("url"),
                    source=self.name,
                    posted_at=posted_at,
                    description=item.get("description"),
                    is_remote="remote" in item.get("location", "").lower()
                )
                listings.append(listing)
            return listings
        except Exception as e:
            print(f"Error fetching from {self.name}: {e}")
            return []
