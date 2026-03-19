from datetime import datetime, timedelta, timezone
from typing import List
from backend.models import JobListing, SearchConfig


class JobProcessor:
    @staticmethod
    def process(listings: List[JobListing], config: SearchConfig) -> List[JobListing]:
        # 1. Deduplication based on URL
        seen_urls: set = set()
        unique_listings: List[JobListing] = []
        for job in listings:
            if job.url not in seen_urls:
                unique_listings.append(job)
                seen_urls.add(job.url)

        now_utc = datetime.now(timezone.utc)

        # 2. Recency filtering — normalize naive datetimes to UTC before comparing
        cutoff_date = now_utc - timedelta(days=config.days_limit)
        filtered_listings = []
        for job in unique_listings:
            posted = job.posted_at
            if posted.tzinfo is None:
                posted = posted.replace(tzinfo=timezone.utc)
            if posted >= cutoff_date:
                filtered_listings.append(job)

        # 3. Remote detection reinforcement
        for job in filtered_listings:
            if not job.is_remote:
                loc = job.location.lower()
                desc = (job.description or "").lower()
                remote_terms = ["remote", "telework", "work from home", "anywhere"]
                if any(t in loc or t in desc for t in remote_terms):
                    job.is_remote = True

        # 4. Match scoring
        for job in filtered_listings:
            score = 0
            posted = job.posted_at
            if posted.tzinfo is None:
                posted = posted.replace(tzinfo=timezone.utc)

            # Recency bonus: +10 if posted within 48 hours
            if posted >= (now_utc - timedelta(hours=48)):
                score += 10
                job.tags.append("Recent")

            # Target company bonus: +5
            if any(company.lower() in job.company.lower() for company in config.target_companies):
                score += 5
                job.tags.append("Target Company")

            # High-match keywords: +3 per keyword found in title or description
            text_to_scan = (job.title + " " + (job.description or "")).lower()
            for kw in config.high_match_keywords:
                if kw.lower() in text_to_scan:
                    score += 3
                    job.tags.append(kw)

            # Remote bonus: +2
            if job.is_remote:
                score += 2
                job.tags.append("Remote")

            job.match_score = score

        # Sort descending by match score
        filtered_listings.sort(key=lambda x: x.match_score, reverse=True)
        return filtered_listings
