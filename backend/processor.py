from datetime import datetime, timedelta
from typing import List
from backend.models import JobListing, SearchConfig

class JobProcessor:
    @staticmethod
    def process(listings: List[JobListing], config: SearchConfig) -> List[JobListing]:
        # 1. Deduplication based on URL
        seen_urls = set()
        unique_listings = []
        for job in listings:
            if job.url not in seen_urls:
                unique_listings.append(job)
                seen_urls.add(job.url)

        # 2. Recency Filtering
        cutoff_date = datetime.now() - timedelta(days=config.days_limit)
        filtered_listings = [
            job for job in unique_listings 
            if job.posted_at >= cutoff_date
        ]

        # 3. Remote Detection (already partially done in adapters, but can be reinforced)
        for job in filtered_listings:
            if not job.is_remote:
                if any(term in job.location.lower() for term in ["remote", "telework", "work from home", "anywhere"]):
                    job.is_remote = True
                elif job.description and any(term in job.description.lower() for term in ["remote", "telework", "work from home", "anywhere"]):
                    job.is_remote = True

        # 4. Match Scoring
        for job in filtered_listings:
            score = 0
            
            # Recency bonus: +10 if posted in last 48 hours
            if job.posted_at >= (datetime.now() - timedelta(hours=48)):
                score += 10
                job.tags.append("Recent")

            # Target company bonus: +5
            if any(company.lower() in job.company.lower() for company in config.target_companies):
                score += 5
                job.tags.append("Target Company")

            # High match keywords: +3 per keyword
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

        # Sort by Match Score (descending)
        filtered_listings.sort(key=lambda x: x.match_score, reverse=True)
        
        return filtered_listings
