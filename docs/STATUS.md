# Session Status — Jobsearch

## Current Session (2026-03-19)
- Bug fixes applied to initial Gemini codebase (Claude Code review):
  - arbeitnow.py: fixed date parsing (Unix timestamp) and keyword matching (OR-phrase, title+description)
  - processor.py: fixed timezone-aware vs naive datetime comparison throughout
  - requirements.txt: removed asyncio (stdlib, not a pip package)
- Added TheMuseAdapter (no API key required)
- Confirmed: free/no-auth sources (Arbeitnow, The Muse, RemoteOK) have poor quality for
  executive-level US remote ops/strategy roles
- Script is functional and ready — blocked on API keys for useful output

## Project State
- Foundation: [X]
- Environment: [X]
- Harvester Core: [X]
- TheMuseAdapter: [X] (low yield — retail-heavy without category filtering)
- ArbeitnowAdapter: [X] (European only — near-zero value for US search)
- AdzunaAdapter: [X] (Awaiting Keys — HIGHEST PRIORITY)
- USAJobsAdapter: [X] (Awaiting Keys — second priority, good for federal roles)
- JoobleAdapter: [X] (Awaiting Keys)
- Frontend: [ ]
- Database: [ ]

## Pending Tasks
- [ ] GET ADZUNA KEY: developer.adzuna.com — free, 5 min, no credit card
- [ ] GET USAJOBS KEY: developer.usajobs.gov/APIRequest/Index — free, 10 min government form
- [ ] Add keys to .env and run first live harvest
- [ ] Evaluate output quality; refine keyword list and scoring weights
- [ ] Consider adding more sources once baseline is working

## Known Good Run Command
source ~/miniconda3/etc/profile.d/conda.sh
conda run -n jobsearch python main.py \
  --keywords "Chief of Staff, Director Operations, Operational Excellence, Business Transformation, Workforce Planning, Data Scientist, Six Sigma" \
  --location "Remote" \
  --days 14 \
  --output output/job_leads_$(date +%Y%m%d).csv
