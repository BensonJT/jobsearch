# Jobsearch — Claude Working Agreement

## Active Memory Files (loaded at session start)
@/docs/STATUS.md

## North Star (do not optimize away)
Jobsearch simplifies and automates the process of finding and applying for jobs,
leveraging intelligent search and application tracking to help the user manage
their career growth efficiently.

## Current Scope
- Phase 1 complete: Modular job harvester with 4 API adapters (Arbeitnow, Adzuna, Jooble, USAJobs)
- Phase 2 pending: Obtain API keys and validate live adapter output
- Phase 3 pending: Bug fixes identified (see Known Issues below)
- Frontend/dashboard not yet started

## Known Issues (fix before Phase 2 work)
1. **Arbeitnow date bug (HIGH):** adapter hardcodes `datetime.now()` for all records instead of
   parsing the actual `created_at` field (Unix timestamp). Every Arbeitnow job gets the +10
   recency bonus incorrectly, inflating match scores.
2. **Arbeitnow keyword match (HIGH):** uses exact substring match on title only. Misses any
   job that doesn't contain the exact search phrase. Should split keywords and use OR logic,
   and/or also scan the description field.
3. **Timezone mismatch (MEDIUM — will crash on first live Adzuna/USAJobs run):**
   Adzuna and USAJobs parse ISO 8601 dates as timezone-aware datetimes. The processor's
   recency filter uses `datetime.now()` (timezone-naive). Comparing aware vs. naive datetimes
   raises a TypeError. Fix: use `datetime.now(timezone.utc)` throughout, or strip tz info on ingest.
4. **asyncio in requirements.txt (LOW):** asyncio is Python stdlib — removing it from
   requirements.txt avoids a confusing pip install failure.

## Repo map (where to look first)
- Entry point: `main.py` (CLI args, CSV export)
- Data models: `backend/models.py` (JobListing, SearchConfig)
- Orchestrator: `backend/harvester.py` (asyncio.gather across all adapters)
- Post-processing: `backend/processor.py` (dedup, recency filter, scoring, sort)
- Adapters: `backend/adapters/` (base.py, adzuna.py, arbeitnow.py, jooble.py, usajobs.py)
- Docs: `docs/STATUS.md` (session state)

## Local environment
Xubuntu Linux (optiplex) · conda env `jobsearch` · Python 3.12+
Run: `source ~/miniconda3/etc/profile.d/conda.sh && conda run -n jobsearch python main.py --keywords ... --location Remote`

## Session continuity (STATUS.md)
`docs/STATUS.md` is the session state file — read it first, update it last.
- **Start:** Output the SESSION START CONFIRMATION block before doing anything else
- **End:** Overwrite STATUS.md with current state snapshot (git history is the changelog)
- Do not wait to be asked — updating STATUS.md is part of wrapping up, same as a commit
- Keep it concise — bullet points preferred over prose

## Sprint Plan (when active)
If `docs/SPRINT_PLAN.md` exists, it is a binding contract.
- Execute tasks in checklist order — do not reorder without explicit user confirmation
- Write the finalized plan to `docs/SPRINT_PLAN.md` using the established structure
- Restore `@/docs/SPRINT_PLAN.md` in the Active Sprint section of `docs/STATUS.md`

## When uncertain
- Ask a single focused question, then proceed with a reasonable default.

## Coding standards
- Python: follow PEP 8; use type hints where practical; keep functions readable;
  add concise comments/docstrings.
- Prefer "boring, maintainable" implementations over novel ones.

## Git commits:
- After completing any meaningful unit of work, commit locally with a
  descriptive commit message.
- Commit message format:
  - First line: short summary in imperative mood, max 72 chars
  - Blank line
  - Body: 2-5 bullets explaining what changed and why
- Group related changes into one commit.
- Do NOT push to GitHub — the user handles all pushes.
