# Session Status — Jobsearch

_Last updated: 2026-09-15 ~09:30 ET (Claude Code on Vostro). Overwrite at the end of each session; git history is the changelog._

## ⚠️ Running right now (check first)

A chained JD backfill started 2026-09-15 07:42 ET, plus a queued Amentum ingest. Both run in the background on Vostro via `nohup`, so they survive clearing the Claude context but **not** a reboot, WSL shutdown, or OOM.

| Order | Stage | Command inside the chain | State at 09:25 |
|---|---|---|---|
| 1 | Oracle, all titles | `sweep_ats.py --skip-sweep --platform oracle_orc --detail-budget 16000 --detail-all --workers 6` | Running. Only Marriott is left, at 7,800 / 9,735. Run total: 13,269 JDs, 168 postings found taken down, 24 errors. |
| 2 | Workday, prefiltered titles | `sweep_ats.py --skip-sweep --platform workday --detail-budget 5000 --workers 6` | Queued |
| 3 | Workday, all titles | `sweep_ats.py --skip-sweep --platform workday --detail-budget 50000 --detail-all --workers 6` | Queued, many hours (CVS alone is a very large board) |
| 4 | Amentum ingest | `sweep_ats.py --employer amentum --detail-budget 3000 --detail-all --workers 6` | Waits for `=== DONE` in the backfill log, then runs |

**Check progress:**
```bash
cd ~/code/jobsearch
grep '^===' output/backfill_20260915_day.log        # which stage; "=== DONE" when stages 1-3 finish
tail -3 output/backfill_20260915_day.log
tail -3 output/amentum_ingest_20260915.log          # "=== AMENTUM DONE" when stage 4 finishes
ps -eo pid,etime,cmd | grep -E '[r]un_backfill_day|[a]fter_backfill_amentum|[s]weep_ats.py'
```

**While these run:** DuckDB allows one writer, so do not open `db/jobsearch.duckdb` in another process, even read-only (the open fails), and do not start another sweep. Queries have to wait.

**If the machine restarted mid-run:** nothing is lost beyond the last unsaved chunk, because the detail stage commits every 100 JDs per board. Rerun whatever stage was interrupted. Postings that already have a JD are skipped automatically. The chain scripts are `output/run_backfill_day.sh` and `output/after_backfill_amentum.sh` (gitignored).

**After everything finishes:** check coverage.
```sql
SELECT platform, count(*) FILTER (WHERE description_text IS NOT NULL) AS with_jd,
       count(*) AS active, count(*) FILTER (WHERE description_text IS NULL) AS missing
FROM vw_active GROUP BY 1 ORDER BY active DESC;
SELECT * FROM vw_board_health WHERE NOT ok;
```
Baseline before today's backfill (morning of 2026-09-15): 78,154 active postings, 13,061 with a JD. Every Greenhouse, Lever, Ashby and BambooHR posting already had one. Missing: Workday 48,527, Oracle 15,396, SmartRecruiters 1,048, Workable 122.

## What this session did (2026-09-14 → 09-15)

### Audit → ingestion rebuilt to spec
The first full run on 2026-09-14 completed (126 boards, 18,093 postings, 23.3 min) before an unrelated OOM crash. The audit found:
- **~60% of runtime was DuckDB per-row autocommit** over the WSL 9p mount to the E: drive.
- **The 1,000-job cap falsely closed postings** on large boards.
- **`posted_at` was collected and then dropped.**
- **Workday and Oracle rows had no JD** and collapsed locations.

Rebuilt `backend/ats/`:
- **Whole-board pulls, no cap, 8 boards in parallel.** `--max-pages` is only a safety valve, and a truncated pull skips the close pass.
- **One transaction per board** through a staging table with `INSERT … ON CONFLICT DO UPDATE`. A req is updated in place and never re-added. It is closed (`closed_at`) the first clean run it's missing, reopened if it returns, and never deleted, so the JD corpus accumulates for later TF-IDF work.
- **Schema v2**, one normalized `postings` table: location_primary, locations (JSON), country, workplace_type, employment_type, job_family, job_level, pay_* with pay_source, posted_at, posting_end_at, description_fetched_at, and raw_json holding the platform record verbatim. Migration from v1 was automatic. A `.v1-backup-20260915` copy sits beside the DB and can be deleted.
- **Views and parameterized macros** in `store.py`: `new_postings(days)`, `posted_within(days)`, `taken_down(days)`, `title_match(regex)`, `title_match_new(regex, days)`, `text_match(regex)`, `vw_active`, `vw_remote_active`, `vw_dmv_or_remote_active`, `vw_board_health`, `vw_posting_lifetimes`, `vw_pay_annualized`.
- **Adapters:** Workday, Oracle ORC, Greenhouse, Lever, Ashby, plus new Workable, BambooHR and SmartRecruiters. The faith boards from the vault's daily faith sweep are now in the DB too. Retries on transient errors. Workday underscore tenants are reached via `wdN.myworkdaysite.com`. Oracle accepts an empty site number, which means the tenant's default site.
- **Detail stage:** new postings get their JD automatically (`--new-detail-cap`, default 5000, every title). The older backlog then gets `--detail-budget` (default 300, newest first, prioritized by the regex in `prefilter.py`). A 404 on detail closes the posting. Commits happen every 100 JDs.
- **Tests:** `tests/test_ats.py`, 11 passing, no network.
- **Full run after the rebuild:** 17.4 min, 124 of 125 boards ok, 76,431 live postings, 111 taken down.

### Registry fixes (the CSV lives in the vault, outside this repo)
- **Single registry file as of 09-15 ~10:00:** `ats_registry_candidates.csv` was merged into `ats_registry.csv` (174 rows, 133 sweepable, verified identical to the two-file load) and deleted. The loader no longer reads a candidates file.
- **Resolved:** General Motors `Careers_GM`, Philips `jobs-and-careers`, Wells Fargo (tenant returns `total=0` after page 1, fixed in the adapter), CFA Institute, Forward Financing (slug with a space), SAIC (empty Oracle site).
- **Added:** Credence (Workable) and Amentum (Workday `pae` / `wd1` / `Amentum_Careers`, 2,756 live). amentumcareers.com is a Clinch front end behind AWS WAF, and the iCIMS site is retired.
- **Removed as duplicates:** Optum (was pointed at Michael Baker's Oracle host) and Meridial (Invisible's board). Alma is folded into Spring Health (`springhealth66`).
- **Registry now sweeps ~133 boards:** Workday 55, Greenhouse 38, Ashby 14, Oracle 10, Lever 7, SmartRecruiters 4, BambooHR 3, Workable 2.

### Public GitHub prep
- **`origin` = git@github.com:BensonJT/jobsearch.git** (public). `optiplex-backup` remains the one-way backup.
- **Personal data is out of the repo.** Pay thresholds and home location live in gitignored `backend/profile_local.py`, with a neutral template at `profile_local.example.py`. Registry and dedup paths live in gitignored `.env` (`JOBSEARCH_REGISTRY_DIR`, `JOBSEARCH_VAULT_DIR`). Forbidden terms live in gitignored `.personal_patterns`, and the pre-commit scan is in CLAUDE.md. `docs/archive/` and old output CSVs are deleted.
- **History squashed to one root commit `6fde054`** and force-pushed. GitHub, Vostro and OptiPlex were each verified at one clean commit. The pre-squash backup `~/code/jobsearch_history_backup_20260915.bundle` still contains personal history. Keep it off GitHub and delete it when no longer needed.
- **README rewritten** for a public audience: how a run works, platforms, finding registry identifiers, querying, schema, performance, limitations, responsible use. `.env.template` rewritten to match what the code reads.
- The old March `main.py` harvester stack was deleted.

## Pending / next session
- [ ] **Confirm the backfill chain and Amentum ingest finished**, then run the coverage query above.
- [ ] **Push local commits** (`git push`; plain push, no force needed now).
- [ ] **Screen engine:** run `backend/screen.py` rules against `postings` → `screen_verdict` / `screen_score`. Build the SQL views/macros for job scenarios on top.
- [ ] **Daily schedule** for the full sweep (cron / Task Scheduler). A normal day fetches only that day's new JDs.
- [ ] **Long tail:** iCIMS (8 employers, bot check), Dayforce (blocked), and Taleo/Eightfold/Phenom/SuccessFactors/ADP/UKG/Paylocity (no adapter yet).
- [ ] **Registry gaps:** 7 "generic slug, VERIFY" Ashby/Greenhouse rows (Summer and Tilt look like the wrong company). ProSidian's SmartRecruiters id is unresolved. Generic front-door URLs (ADP, Paylocity, SuccessFactors, Dayforce, AppOne) need company-specific URLs.
- [ ] **Aggregator keys** (Adzuna, Jooble, USAJobs) aren't in Vostro's `.env`, so `sweep.py` skips all three there. Copy them from OptiPlex if that sweep is wanted on Vostro.
- [ ] **Consider generating the vault's daily faith-board markdown from the DB** instead of the separate `faith_board_sweep.py`.
- [ ] **Cleanup:** delete `db/jobsearch.duckdb.v1-backup-20260915` and, when comfortable, the history bundle.

## Run
```bash
.venv/bin/python sweep_ats.py                                   # full sweep + new-posting JDs + 300 backlog JDs
.venv/bin/python sweep_ats.py --employer "capital one"          # one employer
.venv/bin/python sweep_ats.py --skip-sweep --detail-budget 5000 --detail-all   # backlog JDs only
.venv/bin/python -m pytest -q                                   # tests
./run_sweep.sh [days]                                           # aggregator pre-screen (needs keys in .env)
```
