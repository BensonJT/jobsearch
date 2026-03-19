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
    # High-match keywords add +3 bonus on top of standard keyword scoring.
    # Keep these specific to Jeff's differentiators — avoid generic terms like
    # "Python" which match developer jobs unrelated to his target roles.
    high_match_keywords: list[str] = [
        "LSSBB", "Lean Six Sigma", "Workforce Planning", "Chief of Staff",
        "GenAI", "Business Transformation", "Capacity Management",
        "Organizational Effectiveness", "Change Management", "PMO",
        "Scrum Master", "Operational Excellence"
    ]
    target_companies: list[str] = [
        "RTX", "Raytheon", "Pratt & Whitney", "Collins Aerospace",
        "Microsoft", "Mastercard", "Capital One", "JPMorgan Chase",
        "Booz Allen Hamilton", "Leidos", "Lockheed Martin", "L3Harris",
        "Humana", "Novartis", "General Motors", "ServiceNow",
        "NVIDIA", "OpenAI", "Anthropic", "Google", "DeepMind"
    ]
