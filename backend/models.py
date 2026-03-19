from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, HttpUrl

class JobListing(BaseModel):
    title: str
    company: str
    location: str
    url: str
    source: str
    posted_at: datetime
    description: Optional[str] = None
    salary: Optional[str] = None
    is_remote: bool = False
    match_score: int = 0
    tags: list[str] = Field(default_factory=list)

class SearchConfig(BaseModel):
    keywords: str
    location: Optional[str] = "Remote"
    days_limit: int = 7
    min_salary: Optional[int] = None
    high_match_keywords: list[str] = [
        "LSSBB", "Python", "Workforce Planning", "Chief of Staff", 
        "GenAI", "Business Transformation", "Capacity Management"
    ]
    target_companies: list[str] = [
        "NVIDIA", "OpenAI", "Anthropic", "ServiceNow", "Microsoft",
        "Mastercard", "Capital One", "JPMorgan Chase",
        "Booz Allen Hamilton", "Leidos", "Lockheed Martin"
    ]
