# Session Status — Jobsearch

## Current Session (2026-03-19)
- Bug fixes applied to initial Gemini codebase (Claude Code review):
  - arbeitnow.py: fixed date parsing (Unix timestamp) and keyword matching (OR-phrase, title+description)
  - processor.py: fixed timezone-aware vs naive datetime comparison throughout
  - requirements.txt: removed asyncio (stdlib, not a pip package)
- Added TheMuseAdapter (no API key required)
- PostgreSQL Integration Added:
  - New module `backend/database.py` created for upserting listings.
  - CLI flags `--db` and `--new-only` implemented in `main.py`.
  - Database connection details identified from `Environment_Map.md`:
    - Host: `localhost`, Port: `5432`, User: `postgres`, Password: `PostgreSQL16`
    - Connection string: `postgresql://postgres:PostgreSQL16@localhost:5432/jobsearch`
  - Scoring logic updated: Title match (3x), Description match (1x).
- Confirmed: free/no-auth sources (Arbeitnow, The Muse, RemoteOK) have poor quality for
  executive-level US remote ops/strategy roles
- Script is functional and verified with Adzuna and USAJobs API keys.

## Project State
- Foundation: [X]
- Environment: [X]
- Harvester Core: [X]
- TheMuseAdapter: [X]
- ArbeitnowAdapter: [X]
- AdzunaAdapter: [X] (Verified Live)
- USAJobsAdapter: [X] (Verified Live)
- JoobleAdapter: [X] (Awaiting Keys)
- Frontend: [ ]
- Database: [X] (PostgreSQL integration complete)

## Completed Tasks (2026-03-19)
- [X] PostgreSQL Database Integration:
  - Schema created (`job_listings` table).
  - Upsert logic implemented to preserve `status`.
  - CLI flags `--db` and `--new-only` added.
- [X] Enhanced Scoring Logic:
  - Title matches weighted 3x.
  - Description matches weighted 1x.
- [X] First Live Harvest Run:
  - Confirmed Adzuna and USAJobs keys work.
  - Populated `job_listings` with 300+ executive-level leads.
- [X] Description Truncation Removed.
- [X] Environment Mapping:
  - Identified primary PostgreSQL role (`postgres`) and credentials from Keystone.

## Pending Tasks
- [ ] GET JOOBLE KEY (if still needed)
- [ ] Evaluate output quality; refine keyword list and scoring weights
- [ ] Consider adding more sources once baseline is working

## Known Good Run Command
source ~/miniconda3/etc/profile.d/conda.sh
conda run -n jobsearch python main.py \
  --keywords "Chief of Staff, Director Operations, Operational Excellence, Business Transformation, Workforce Planning, Data Scientist, Six Sigma" \
  --location "Remote" \
  --days 14 \
  --output output/job_leads_$(date +%Y%m%d).csv
