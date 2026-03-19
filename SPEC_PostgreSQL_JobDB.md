# Build Spec: PostgreSQL Job Listings Database
**For:** Gemini (autonomous build)
**Reviewed by:** Claude (cleanup pass after Gemini completes)
**Date:** 2026-03-19
**Codebase:** `/home/jeff/code/jobsearch/`

---

## What Already Exists (Read Before Touching Anything)

The jobsearch script is a working multi-source job harvester. Do NOT break existing behavior.

**Current flow:**
1. `main.py` parses CLI args → builds `SearchConfig`
2. `JobHarvester` calls 5 adapters async → returns `List[JobListing]`
3. `JobProcessor.process()` deduplicates, filters by recency, scores, sorts
4. `main.py` exports to CSV

**Working adapters:** Adzuna, Jooble, USAJobs, TheMuse, Arbeitnow
**Conda env:** `jobsearch` (Python 3.x, httpx, pandas, python-dotenv already installed)
**Credentials:** All in `.env` file — do NOT modify `.env`

---

## What to Build

### Goal
Store full job descriptions in PostgreSQL so listings can be:
1. Scored against description text (not just title)
2. Persisted across multiple harvest runs (no duplicates)
3. Triaged with a `status` field (`new` / `reviewed` / `applied` / `pass`)

### Do NOT Change
- CSV export behavior — `--output` flag must keep working exactly as before
- Any adapter's API endpoint, auth, or HTTP logic
- The `.env` file
- `backend/models.py` (unless adding optional fields only)
- `backend/harvester.py`

---

## Step-by-Step Build Instructions

### Step 1: Add DATABASE_URL to .env (instructions only — do not edit .env yourself)

Tell the user to add this line to `.env`:
```
DATABASE_URL=postgresql://jeff@localhost/jobsearch
```
Create the database first:
```bash
createdb jobsearch
```

### Step 2: Create `backend/database.py`

New file. Responsibilities:
- Connect to PostgreSQL using `DATABASE_URL` from environment
- Create the `job_listings` table if it does not exist (idempotent)
- Upsert job listings (insert or update on url conflict)
- Provide a `get_new_listings()` function for future use

**Schema:**
```sql
CREATE TABLE IF NOT EXISTS job_listings (
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

**Upsert logic:** On conflict (url), update title, company, match_score, description, harvested_at. Do NOT overwrite `status` — preserve any human-set status value.

**Use:** `psycopg2-binary` (synchronous is fine — DB write happens after all async fetching completes).

**Connection pattern:**
```python
import os, psycopg2
from psycopg2.extras import execute_values

def get_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

def ensure_schema():
    """Create table if not exists. Call once at startup."""
    ...

def upsert_listings(listings: list, search_keywords: str):
    """Upsert a list of JobListing objects. Preserve existing status values."""
    ...

def get_new_listings() -> list:
    """Return all rows with status='new', ordered by match_score DESC."""
    ...
```

### Step 3: Remove Description Truncation in Adapters

In each adapter below, remove the `[:500]` slice (or whatever truncation exists) on the description field. Let the API return whatever it returns — the DB can hold full text.

Files to update:
- `backend/adapters/adzuna.py` — `description=description[:500]` → `description=description`
- `backend/adapters/jooble.py` — `description=job.get("snippet", "")` is fine, just don't truncate
- `backend/adapters/usajobs.py` — `description=desc.get("QualificationSummary", "")[:500]` → remove `[:500]`
- `backend/adapters/themuse.py` — `description=description[:500]` → `description=description`

### Step 4: Fix Match Scoring in `backend/processor.py`

**Current problem:** Title match and description match are weighted equally. "Branch Manager" scores 12 because "Manager" appears 12 times in a description. Fix: title matches should count 3x more than description matches.

**Current scoring logic** (find it and replace it):
The current logic counts how many keyword phrases appear in `(title + description).lower()`.

**New scoring logic:**
```python
score = 0
title_lower = job.title.lower() if job.title else ""
desc_lower = job.description.lower() if job.description else ""

for phrase in keyword_phrases:
    if phrase in title_lower:
        score += 3   # title match worth 3x
    elif phrase in desc_lower:
        score += 1   # description match worth 1x

job.match_score = score
```

This ensures a job with 3 keyword phrases matching the title scores 9 before description is even checked — pushing real matches above noise.

### Step 5: Update `main.py`

Add two new optional CLI arguments:

```python
parser.add_argument("--db", action="store_true", help="Write results to PostgreSQL database")
parser.add_argument("--new-only", action="store_true", help="Only show/export listings with status=new from DB")
```

**When `--db` is passed:**
1. Call `ensure_schema()` at startup
2. After `JobProcessor.process()`, call `upsert_listings(processed_listings, config.keywords)`
3. Print: `"Upserted N listings to database."`
4. Still export to CSV as normal (do not skip CSV when --db is used)

**When `--new-only` is passed (requires --db):**
1. After upsert, call `get_new_listings()`
2. Export only those rows to the CSV (or print to stdout if no --output given)
3. Print count of new vs. total

### Step 6: Update `requirements.txt`

Add:
```
psycopg2-binary>=2.9
```

### Step 7: Update `GEMINI.md`

Add a section documenting:
- The new `--db` and `--new-only` flags
- The database schema
- The `backend/database.py` module
- The improved scoring logic (title 3x vs description 1x)

---

## Test Plan (Run After Building)

```bash
# 1. Create the database
createdb jobsearch

# 2. Add DATABASE_URL to .env
echo "DATABASE_URL=postgresql://jeff@localhost/jobsearch" >> .env

# 3. Run with --db flag
source ~/miniconda3/etc/profile.d/conda.sh
conda run -n jobsearch python main.py \
  --keywords "Chief of Staff,Program Manager,Workforce Planning" \
  --location "Remote" \
  --days 30 \
  --db \
  --output /tmp/test_db_run.csv

# 4. Verify DB has rows
psql jobsearch -c "SELECT count(*), status FROM job_listings GROUP BY status;"

# 5. Run again — verify no duplicate rows
conda run -n jobsearch python main.py \
  --keywords "Chief of Staff,Program Manager,Workforce Planning" \
  --location "Remote" \
  --days 30 \
  --db \
  --output /tmp/test_db_run2.csv

psql jobsearch -c "SELECT count(*) FROM job_listings;"
# Should be same count (upsert, not insert)

# 6. Check top results have relevant titles
psql jobsearch -c "SELECT match_score, title, company, source FROM job_listings ORDER BY match_score DESC LIMIT 20;"
```

---

## Files to Create or Modify (Summary)

| File | Action | Notes |
|---|---|---|
| `backend/database.py` | CREATE | PostgreSQL upsert, schema, get_new_listings |
| `backend/adapters/adzuna.py` | MODIFY | Remove description truncation |
| `backend/adapters/jooble.py` | MODIFY | Remove description truncation if present |
| `backend/adapters/usajobs.py` | MODIFY | Remove description truncation |
| `backend/adapters/themuse.py` | MODIFY | Remove description truncation |
| `backend/processor.py` | MODIFY | Title 3x scoring fix |
| `main.py` | MODIFY | --db and --new-only flags |
| `requirements.txt` | MODIFY | Add psycopg2-binary |
| `GEMINI.md` | MODIFY | Document new capabilities |

---

## Guard Rails for Gemini

1. Do NOT modify `.env` directly — write instructions for the user instead
2. Do NOT change adapter API endpoints, auth, or HTTP request logic
3. Do NOT break the CSV export — `--output` must keep working without `--db`
4. Do NOT use async database calls — synchronous psycopg2 is correct here
5. Do NOT touch `backend/models.py` unless you only need to add optional fields with defaults
6. If psycopg2 is not installed in the `jobsearch` conda env, add it via: `conda run -n jobsearch pip install psycopg2-binary`
7. The `status` field in the DB must never be overwritten on upsert — humans set it manually

---

## Claude's Cleanup Pass Will Check

After Gemini builds, Claude will:
- Verify the upsert does not overwrite `status`
- Confirm the scoring fix produces sane results on a live harvest
- Check that `--db` and non-`--db` runs both produce correct CSV output
- Add any missing error handling (e.g., DB connection failure should not crash the whole harvest — catch and warn)
- Review `database.py` for SQL injection risks (use parameterized queries, not f-strings)

