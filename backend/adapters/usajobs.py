import os
from typing import List
from datetime import datetime, timezone
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
            "Authorization-Key": self.api_key,
        }

        # USAJobs keyword search works best with one phrase at a time.
        keyword_phrases = [kw.strip() for kw in config.keywords.split(",") if kw.strip()]
        seen_urls: set = set()
        all_listings: List[JobListing] = []

        for phrase in keyword_phrases:
            params = {
                "Keyword": phrase,
                "ResultsPerPage": 25,
                "RemoteIndicator": "True",
            }
            try:
                data = await self._get(self.url, params=params, headers=headers)
                items = data.get("SearchResult", {}).get("SearchResultItems", [])
                for item in items:
                    desc = item.get("MatchedObjectDescriptor", {})
                    uri = desc.get("PositionURI", "")
                    if not uri or uri in seen_urls:
                        continue
                    seen_urls.add(uri)

                    try:
                        posted_at = datetime.fromisoformat(
                            desc.get("PublicationStartDate", "").replace("Z", "+00:00")
                        )
                    except (ValueError, TypeError):
                        posted_at = datetime.now(timezone.utc)

                    location = desc.get("PositionLocation", [{}])[0].get("LocationName", "")
                    telework = desc.get("PositionOfferingType", [{}])

                    all_listings.append(JobListing(
                        title=desc.get("PositionTitle", ""),
                        company=desc.get("OrganizationName", ""),
                        location=location,
                        url=uri,
                        source=self.name,
                        posted_at=posted_at,
                        salary=str(desc.get("PositionRemuneration", [{}])[0].get("MinimumRange", "")),
                        is_remote=(
                            "anywhere" in location.lower() or
                            "remote" in location.lower() or
                            "remote" in desc.get("PositionTitle", "").lower()
                        ),
                        description=desc.get("QualificationSummary", ""),
                    ))
            except Exception as e:
                print(f"Error fetching from {self.name} (phrase='{phrase}'): {e}")

        return all_listings
