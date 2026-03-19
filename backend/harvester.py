import asyncio
from typing import List
from backend.models import JobListing, SearchConfig
from backend.adapters.base import BaseAdapter
from backend.adapters.adzuna import AdzunaAdapter
from backend.adapters.arbeitnow import ArbeitnowAdapter
from backend.adapters.jooble import JoobleAdapter
from backend.adapters.usajobs import USAJobsAdapter
from backend.adapters.themuse import TheMuseAdapter


class JobHarvester:
    def __init__(self):
        self.adapters: List[BaseAdapter] = [
            TheMuseAdapter(),
            ArbeitnowAdapter(),
            AdzunaAdapter(),
            JoobleAdapter(),
            USAJobsAdapter(),
        ]

    async def fetch_all(self, config: SearchConfig) -> List[JobListing]:
        tasks = [adapter.search(config) for adapter in self.adapters]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_listings = []
        for result in results:
            if isinstance(result, list):
                all_listings.extend(result)
            elif isinstance(result, Exception):
                print(f'An adapter failed: {result}')

        return all_listings
