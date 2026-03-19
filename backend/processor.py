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
        keyword_phrases = [kw.strip().lower() for kw in config.keywords.split(",") if kw.strip()]
        
        for job in filtered_listings:
            score = 0
            title_lower = job.title.lower() if job.title else ""
            desc_lower = job.description.lower() if job.description else ""
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

            # Keyword match scoring: Title (3x) vs Description (1x)
            for phrase in keyword_phrases:
                if phrase in title_lower:
                    score += 3
                    if phrase not in job.tags:
                        job.tags.append(phrase)
                elif phrase in desc_lower:
                    score += 1
                    if phrase not in job.tags:
                        job.tags.append(phrase)

            # High-match keywords bonus: +3 (if found in title or description)
            # Keeping this as a separate bonus category from SearchConfig
            text_to_scan = (title_lower + " " + desc_lower)
            for kw in config.high_match_keywords:
                if kw.lower() in text_to_scan:
                    score += 3
                    if kw not in job.tags:
                        job.tags.append(kw)

            # Remote bonus: +2
            if job.is_remote:
                score += 2
                job.tags.append("Remote")

            job.match_score = score

        # Sort descending by match score
        filtered_listings.sort(key=lambda x: x.match_score, reverse=True)
        return filtered_listings
