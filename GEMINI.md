# Gemini Agent Rules
@CLAUDE.md

## Development Workflow
Follow the rules and conventions established in `CLAUDE.md`.
Use the local environment in Xubuntu Linux (optiplex) and the `jobsearch` conda environment.

## Primary Mandate
Jobsearch automates the search and application lifecycle.
Prioritize clean, maintainable Python code and robust data handling.

## What Gemini Built (2026-03-18 session)
Gemini designed the full architecture and generated the working codebase from SCRIPT_REQUIREMENTS.md.

Architecture decisions that MUST be preserved:
- Modular adapter pattern: each job board is an isolated class inheriting BaseAdapter
- Pydantic models for all data (JobListing, SearchConfig)
- asyncio.gather with return_exceptions=True for fault-isolated parallel fetching
- JobProcessor is stateless (all static methods) — keep it that way
- CSV export via pandas in main.py

## Project Status & Improvements (March 19, 2026)

### Fixed Known Issues
1. **Arbeitnow date parsing:** Fixed to parse Unix timestamp from `created_at`.
2. **Arbeitnow keyword matching:** Broadened to OR-split-keyword search in both title and description.
3. **Timezone consistency:** Standardized on `datetime.now(timezone.utc)` for all comparisons.
4. **Dependencies:** Removed `asyncio` from `requirements.txt`.

### New Capabilities
- **PostgreSQL Integration:** Persistent storage for job listings with "upsert" logic to prevent duplicates.
- **Improved Scoring:** Jobs are now scored with title matches weighted 3x more than description matches.
- **Persistence of Status:** The `status` field in the database (e.g., `new`, `reviewed`, `applied`, `pass`) is preserved across harvest runs.
- **CLI Flags:**
    - `--db`: Enables writing results to the PostgreSQL database.
    - `--new-only`: Filters the export to only include listings with `status='new'` in the database.

### Database Schema & Connection Details
**Connection String:** `postgresql://postgres:PostgreSQL16@localhost:5432/jobsearch`

```sql
CREATE TABLE job_listings (
    id SERIAL PRIMARY KEY,
    url TEXT UNIQUE NOT NULL,
    title TEXT,
    company TEXT,
    location TEXT,
    is_remote BOOLEAN,
    posted_at TIMESTAMPTZ,
    description TEXT,
    salary TEXT,
    source TEXT,
    match_score INTEGER,
    search_keywords TEXT,
    harvested_at TIMESTAMPTZ DEFAULT NOW(),
    status TEXT DEFAULT 'new'
);
```
