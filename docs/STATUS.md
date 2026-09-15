# Session Status — Jobsearch

## 2026-09-15 (Claude Code on Vostro) — ingestion rebuilt to spec
`backend/ats/` rewritten after the 2026-09-14 audit. What changed and why:
- **No job cap.** `MAX_JOBS_PER_BOARD` made the close-pass wrong on the nine boards over
  1,000 postings (anything outside the window looked "taken down"). Whole-board pulls
  now; runtime handled by pulling boards concurrently (`--workers 8`, one host per
  board so politeness holds). `--max-pages` remains as an explicit safety valve that
  marks the pull truncated and skips the close-pass.
- **Writes batched.** Each board's upsert + close-pass is one transaction through a
  staging table with `INSERT ... ON CONFLICT DO UPDATE` (10x faster on the 9p mount;
  ~60% of the first run's 23 min was per-row autocommit).
- **Schema v2** — one normalized `postings` table: `location_primary` / `locations`
  (JSON) / `country` / `workplace_type` (remote|hybrid|onsite) / `employment_type` /
  `job_family` / `job_level` / `pay_*` (+`pay_source`) / `posted_at` / `posting_end_at`
  / `description_fetched_at` / `raw_json` (platform record verbatim). Migration from v1
  is automatic and keeps every row's first_seen_at; backup copy written next to the DB.
- **Dates kept.** `posted_at` from every platform (Workday's "Posted N Days Ago" parsed
  relative to the run; "30+" stays NULL until the detail call supplies `startDate`).
- **Detail stage** (`--detail-budget N`, default 300): fills JD text, all locations,
  dates, pay for Workday / Oracle / Workable postings that lack one, newest first,
  prioritized by `backend/ats/prefilter.py` (a budgeting regex, NOT the screen). A 404
  on detail closes the posting (free liveness check).
- **Views + parameterized macros** in `store.py`: `vw_active`, `vw_remote_active`,
  `vw_dmv_or_remote_active`, `vw_board_health`, `vw_posting_lifetimes`,
  `vw_pay_annualized`; `new_postings(days)`, `posted_within(days)`, `taken_down(days)`,
  `title_match(regex)`, `title_match_new(regex, days)`, `text_match(regex)`.
- **Workable adapter** added (Credence, Stream Data Centers).
- **Bugs fixed:** Wells Fargo 40-job pull (Workday `total=0` after page 1); Ashby slugs
  with spaces (URL-encoded); CFA Institute underscore tenant (served via
  `wdN.myworkdaysite.com`); GM (`Careers_GM`) and Philips (`jobs-and-careers`) site
  slugs; Optum→Michael Baker and Meridial→Invisible registry duplicates removed.
- March-2026 `main.py` stack deleted (git history keeps it).
- Tests: `tests/test_ats.py` (lifecycle, truncation, dedup, views, normalizers).

## 2026-09-15 later — public-repo prep + auto JD fetch
- **New postings get their JD automatically**: each sweep fetches details for every posting first seen that run on Workday/Oracle/Workable/BambooHR/SmartRecruiters (`--new-detail-cap`, default 5000), then the title-prefiltered backlog (`--detail-budget`, default 300).
- **Adapters added**: BambooHR, SmartRecruiters (faith boards now in the DB). Detail stage commits every 100 JDs.
- **Personal data removed from the repo**: pay thresholds + home location moved to gitignored `backend/profile_local.py` (template: `profile_local.example.py`); registry + vault paths moved to `.env`. `docs/archive/` deleted (held location + salary example). History squashed before the first push.
- `origin` remote added (GitHub). README rewritten for a public audience.

## Pending
- [ ] Screen engine (`backend/screen.py`) against `postings` → `screen_verdict`.
- [ ] Long-tail platforms: SmartRecruiters + BambooHR adapters already exist in the
      vault's `faith_board_sweep.py`; iCIMS needs a browser pass (bot check).
- [ ] Daily schedule once a clean full run lands (see README for the command).

## Run
```
.venv/bin/python sweep_ats.py                      # full sweep + 300 JD fetches
.venv/bin/python sweep_ats.py --employer "capital one" --detail-budget 0
.venv/bin/python sweep_ats.py --skip-sweep --detail-budget 1000   # JD backfill
./run_sweep.sh [days]                              # aggregator pre-screen (unchanged)
```
