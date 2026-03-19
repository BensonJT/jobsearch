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

## Known Issues for Gemini to Fix (see CLAUDE.md for details)
Priority order:
1. Arbeitnow date parsing (hardcoded datetime.now() — fix to parse actual created_at Unix timestamp)
2. Arbeitnow keyword matching (exact substring only — broaden to OR-split-keyword search + description scan)
3. Timezone-aware vs naive datetime comparison in processor.py (use datetime.now(timezone.utc) consistently)
4. Remove asyncio from requirements.txt (it is stdlib, not a pip package)
