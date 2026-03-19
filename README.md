# Jobsearch — Intelligence-Led Job Harvester

**Jobsearch** is a high-performance, multi-source job fetching and scoring engine. It automates the discovery of executive-level and specialized roles by querying multiple job board APIs, applying weighted match scoring, and persisting results to a PostgreSQL database for long-term tracking.

---

## Key Features

- **Multi-Source Adapters:** Unified interface for Adzuna, USAJobs, TheMuse, Arbeitnow, and Jooble.
- **Asynchronous Fetching:** Uses `asyncio` and `httpx` to query all sources in parallel for maximum speed.
- **PostgreSQL Persistence:** Permanent storage with "Status-Aware Upserts." Re-running a search updates job details but preserves your manual triage status (`new`, `reviewed`, `applied`, `pass`).
- **Weighted Scoring Engine:** 
    - **Title Matches:** 3x weight for high-signal alignment.
    - **Description Matches:** 1x weight for context.
    - **Bonuses:** Recency (+10 for <48h), Target Companies (+5), and Remote status (+2).
- **Executive-Level Filtering:** Pre-configured for high-impact roles (Chief of Staff, OpEx, Strategy) with deep description scanning.
- **Flexible Export:** Generates clean CSVs for spreadsheet triage or direct database interaction.

---

## Infrastructure & Requirements

- **Platform:** Linux (Optimized for OptiPlex Desktop / WSL2).
- **Environment:** Python 3.12+ (Conda environment `jobsearch`).
- **Database:** PostgreSQL 16.
- **Key Dependencies:** `pandas`, `httpx`, `pydantic`, `psycopg2-binary`, `python-dotenv`.

---

## Setup Instructions

### 1. Environment Setup
```bash
# Create and activate the conda environment
conda create -n jobsearch python=3.12
conda activate jobsearch
pip install -r requirements.txt
```

### 2. Database Initialization
Create the local database:
```bash
createdb jobsearch
```
The schema is automatically managed by the script when using the `--db` flag.

### 3. Configuration (.env)
Create a `.env` file in the root directory:
```env
# Database
DATABASE_URL=postgresql://postgres:PostgreSQL16@localhost:5432/jobsearch

# API Keys
ADZUNA_APP_ID=your_id
ADZUNA_APP_KEY=your_key
USAJOBS_API_KEY=your_key
USAJOBS_EMAIL=your_email
JOOBLE_API_KEY=your_key

# Search Settings
SEARCH_COUNTRY=us
```

---

## Usage

### Basic Harvest (CSV only)
```bash
python main.py --keywords "Chief of Staff, Director Operations" --location "Remote" --days 7 --output leads.csv
```

### Database Integrated Harvest
Fetch and upsert all results to PostgreSQL:
```bash
python main.py --keywords "Data Scientist, Operational Excellence" --db
```

### Review New Leads Only
Fetch results, upsert to DB, and export **only** the jobs you haven't triaged yet:
```bash
python main.py --keywords "Chief of Staff" --db --new-only --output new_leads.csv
```

---

## Architecture

- **`main.py`:** Entry point, CLI argument parsing, and orchestration.
- **`backend/harvester.py`:** Orchestrates parallel fetching across all adapters.
- **`backend/processor.py`:** Handles deduplication, scoring logic, and remote detection reinforcement.
- **`backend/database.py`:** PostgreSQL interaction layer (Schema, Upserts, Status filtering).
- **`backend/adapters/`:** Modular source-specific logic inheriting from `BaseAdapter`.
- **`backend/models.py`:** Pydantic data models for `JobListing` and `SearchConfig`.

---

## Project Status

Managed via `docs/STATUS.md` and `GEMINI.md`. Part of the broader **Keystone LifeOS** ecosystem, designed to feed into the **Resume IDE v2** for automated ATS tailoring.
