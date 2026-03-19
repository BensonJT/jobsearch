import os
from typing import List
from datetime import datetime, timezone
from backend.models import JobListing, SearchConfig
from backend.adapters.base import BaseAdapter


class AdzunaAdapter(BaseAdapter):
    def __init__(self):
        super().__init__("Adzuna")
        self.app_id = os.getenv("ADZUNA_APP_ID")
        self.app_key = os.getenv("ADZUNA_APP_KEY")
        self.country = os.getenv("SEARCH_COUNTRY", "us")
        self.base_url = f"https://api.adzuna.com/v1/api/jobs/{self.country}/search"

    @staticmethod
    def _canonical_url(job_id: str) -> str:
        """Return a stable, session-independent URL using the Adzuna job ID.
        Adzuna redirect_url includes ?se= and ?v= params that change every request,
        breaking URL-based deduplication. The canonical form strips all query params."""
        return f"https://www.adzuna.com/land/ad/{job_id}"

    async def search(self, config: SearchConfig) -> List[JobListing]:
        if not self.app_id or not self.app_key:
            print(f"Adzuna credentials missing, skipping {self.name}")
            return []

        # Adzuna `where` is a geographic location — do NOT pass "Remote" as where.
        # Filter remote client-side instead.
        keyword_phrases = [kw.strip() for kw in config.keywords.split(",") if kw.strip()]

        seen_ids: set = set()
        all_listings: List[JobListing] = []

        for phrase in keyword_phrases:
            params = {
                "app_id": self.app_id,
                "app_key": self.app_key,
                "what": phrase,
                "results_per_page": 50,
            }
            try:
                data = await self._get(f"{self.base_url}/1", params=params)
                results = data.get("results", [])
                for result in results:
                    job_id = str(result.get("id", ""))
                    if not job_id or job_id in seen_ids:
                        continue
                    seen_ids.add(job_id)

                    canonical = self._canonical_url(job_id)

                    try:
                        posted_at = datetime.fromisoformat(
                            result.get("created", "").replace("Z", "+00:00")
                        )
                    except (ValueError, TypeError):
                        posted_at = datetime.now(timezone.utc)

                    loc_name = result.get("location", {}).get("display_name", "")
                    title = result.get("title", "")
                    description = result.get("description", "")
                    is_remote = (
                        "remote" in loc_name.lower() or
                        "remote" in title.lower() or
                        "remote" in description.lower()
                    )

                    all_listings.append(JobListing(
                        title=title,
                        company=result.get("company", {}).get("display_name", "Unknown"),
                        location=loc_name,
                        url=canonical,
                        source=self.name,
                        posted_at=posted_at,
                        salary=str(result.get("salary_min")) if result.get("salary_min") else None,
                        is_remote=is_remote,
                        description=description,
                    ))
            except Exception as e:
                print(f"Error fetching from {self.name} (phrase='{phrase}'): {e}")

        return all_listings
