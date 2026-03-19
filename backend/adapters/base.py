from abc import ABC, abstractmethod
from typing import List
from backend.models import JobListing, SearchConfig
import httpx

class BaseAdapter(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def search(self, config: SearchConfig) -> List[JobListing]:
        """Search for jobs based on the configuration."""
        pass

    async def _get(self, url: str, params: dict = None, headers: dict = None):
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            return response.json()

    async def _post(self, url: str, json_body: dict = None, headers: dict = None):
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=json_body, headers=headers)
            response.raise_for_status()
            return response.json()
