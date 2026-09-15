# Session Status — Jobsearch

_Last updated: 2026-09-15 11:20 EDT (Claude Code on Vostro). Overwrite at the end of each session; git history is the changelog._

## ⚠️ Running right now (check first)

A chained JD backfill started 2026-09-15 07:42 EDT, plus a queued Amentum ingest. Both run in the background on Vostro via `nohup`, so they survive clearing the Claude context but **not** a reboot, WSL shutdown, or OOM.

| Order | Stage | State at 11:16 EDT |
|---|---|---|
| 1 | Oracle, all titles | **Done 09:54.** 15,134 JDs, 214 taken down, 48 errors. |
| 2 | Workday, prefiltered titles | **Done 10:01.** 2,296 JDs, 13 taken down, 33 errors. |
| 3 | Workday, all titles (`--detail-budget 50000 --detail-all`) | **Running.** 29,968 of 46,218 JDs, 96 taken down, 279 errors (<1%, transient per-posting; they stay NULL and a later backlog run retries). ~400 JDs/min, so done ≈ 12:00. CVS Health (15,943) is the long pole. |
| 4 | Amentum ingest (`--employer amentum --detail-all`) | Queued; starts on `=== DONE`, ~10 min. |

**Check progress:**
```bash
cd ~/code/jobsearch
grep '^===' output/backfill_20260915_day.log        # "=== DONE" when stages 1-3 finish
tail -3 output/backfill_20260915_day.log
tail -3 output/amentum_ingest_20260915.log          # "=== AMENTUM DONE" when stage 4 finishes
ps -eo pid,etime,cmd | grep -E '[r]un_backfill_day|[a]fter_backfill_amentum|[s]weep_ats.py'
```

**While these run:** DuckDB allows one writer, so do not open `db/jobsearch.duckdb` in another process, even read-only (the open fails), and do not start another sweep. Scratch-DB work (`--db /some/other/path` + `JOBSEARCH_REGISTRY_DIR` pointing at a scratch registry) is fine and is how the Eightfold/Paylocity adapters were live-tested today.

**If the machine restarted mid-run:** nothing is lost beyond the last unsaved chunk (commits every 100 JDs per board). Rerun the interrupted stage; postings that already have a JD are skipped. Chain scripts: `output/run_backfill_day.sh`, `output/after_backfill_amentum.sh` (gitignored).

**After everything finishes:** run the coverage query. Then a **normal full sweep** (`.venv/bin/python sweep_ats.py`) picks up the four new boards (Microsoft ≈2,240 postings + ~30 min of JDs on its first pass; Omnicell; Liberty Mutual; Logos).
```sql
SELECT platform, count(*) FILTER (WHERE description_text IS NOT NULL) AS with_jd,
       count(*) AS active, count(*) FILTER (WHERE description_text IS NULL) AS missing
FROM vw_active GROUP BY 1 ORDER BY active DESC;
SELECT * FROM vw_board_health WHERE NOT ok;
```
Baseline before today's backfill: 78,154 active, 13,061 with a JD. After it: expect ~60,000+ with a JD.

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
- **Single registry file as of 09-15 ~09:45:** `ats_registry_candidates.csv` was merged into `ats_registry.csv` (174 rows, 133 sweepable, verified identical to the two-file load) and deleted. The loader no longer reads a candidates file.
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

### Eightfold adapter (09-15, ~10:30)
- **New platform `eightfold`** in `backend/ats/adapters.py`: identifier_1 = careers host URL, identifier_2 = company domain. Two list flavors exist and the adapter tries both: `apply/v2/jobs` (Liberty Mutual; Microsoft returns 403) then `pcsx/search` (Microsoft, Omnicell). Both page 10 at a time regardless of `num`. The list JD is a truncated preview, so `apply/v2/jobs/<id>` detail always supplies it (works even where the apply/v2 list is refused). Row key is Eightfold's own posting id; the display job id is reused across locations (21 of Microsoft's 2,240).
- **Page drift:** a single timestamp-ordered pull of Microsoft stored 2,208–2,219 of 2,240 (postings refreshed mid-pull shift the pages). Fix: read in both orders (timestamp, then relevance), union on Eightfold id, and report Truncated (no close pass) if the union is more than 0.5% (min 3) short of the board's count. Microsoft now takes ~200 s per sweep.
- **Live test on a scratch DB:** Omnicell 78, Liberty Mutual 210, Microsoft 2,237 of 2,237–2,240, no duplicates, 0 errors, 30 JDs fetched cleanly. 5 unit tests added (16 total).
- **Registry:** Microsoft and Omnicell rows already had the right identifiers. Liberty Mutual's row was fixed to `https://libertymutual.eightfold.ai` / `libertymutual.com`. First full sweep of Microsoft will fetch up to 2,240 JDs (~30 min at ~75/min).
- **Taleo is not buildable for the registry's employers:** UHG's careersections (10000/10020/10050) all 302 to the Radancy front end at careers.unitedhealthgroup.com (JSON wrapper around rendered HTML, 8.6 MB per page); Centric is Taleo *Business Edition* at `phg.tbe.taleo.net/phg02` (`org=CENTCONS&cws=38`), which serves HTML only. README's unsupported list says so now. A Radancy adapter would cover UHG + L3Harris but means parsing HTML fragments.

### Paylocity adapter (09-15, ~11:05)
- **New platform `paylocity`**: identifier_1 = company GUID, identifier_2 = slug. The documented v2 feed returns an empty list for Faithlife/Logos, so the list stage reads the `window.pageData` JSON block on `recruiting/jobs/All/<guid>/<slug>` (title, location, remote flag, department, date). Its Description is a ~110-char teaser, so the detail stage reads `div.job-preview-details` on each job's Details page (full text, Job Type, pay). A bad GUID 302s to JobNotFound and is raised as a board failure, not an empty board.
- **Live:** Logos Bible Software 6 live, 6 JDs, pay parsed on two ($125–135K Data Scientist US). the user's apply URL carried only the numeric JobId; the GUID came from the Details page's all-jobs link. Registry row updated in the vault (Faithlife LLC is the legal entity). 3 unit tests (19 total).
- **README** now states the one HTML exception honestly (embedded JSON + one description block).

## NEXT SESSION: design the "job finding" layer (the user wants to brainstorm this first)

**The question the user posed (11:20 EDT):** how do we build filtering that replicates what he asks Cowork / Claude Code to do by hand when scanning the JD corpus? i.e. turn "read these 60,000 descriptions and tell me which ones are me" into something that runs in the pipeline.

**What already exists (start from these, don't rebuild):**
- `postings` has reserved columns `screen_verdict`, `screen_score`, `screen_reasons`, `screened_at` — empty so far.
- `backend/screen.py` is a working **card-level** rule engine (verdicts `candidate` / `review` / `reject`, every row keeps reasons) built for the aggregator sweep; `backend/profile.py` holds the vocab: `FUNCTION_PHRASES`, `TITLE_FUNCTION_TERMS`, `PRECISE_TITLE_TERMS`, `JUNIOR_TITLE_TERMS`, `OFF_LANE_TITLE_TERMS`, `PLATFORM_GATED_TERMS`, `PLANT_DISCIPLINE_TERMS`, `CLEARANCE_TERMS`, `ITSM_CHANGE_TERMS`, `HARD_AVOID_INDUSTRY_TERMS`, `AI_GIG_TITLE_TERMS`; pay/location in gitignored `profile_local.py`. It takes a `Listing` dataclass, not a `postings` row — an adapter from row → Listing is the cheap first step.
- `backend/ats/prefilter.py` `DETAIL_TITLE_PATTERN` is the broad title net (budgeting only; it over-includes on purpose).
- SQL macros already do crude finding: `title_match`, `title_match_new`, `text_match(regex)` over title+JD, `vw_pay_annualized`, `vw_dmv_or_remote_active`.
- The vault's `jd_bucketize.py` (resume_ide_v2) extracts JD requirements into buckets with Gemma via Google AI Studio (~2 min/JD) — too slow for 60k, fine for a shortlist.

**Ground truth to load before designing (memory files):** `user_target_role_shape` (ops process excellence, Vz/NFCU shape; NOT product ops / plant-floor CI / domain-gated excellence; travel ≤25%; ≤4 reports), `user_coding_assessment_constraint` (LSS/GPO/BPO/OpsEx is the PRIMARY lane; data/BI secondary and only without an assessment gate), `user_compensation_anchor` ($190K ask), `user_cloud_experience_depth`, `user_bi_tool_stack` (no Power BI/Tableau), `feedback_rejection_patterns` (zero company-level skips), `user_nfcu_office_commute`, `feedback_glassdoor_search_mechanics` (the search strings that work per board are the human version of the rule set).

**Facts that shape the design:**
- Corpus: ~78k active postings across 137 boards, ~60k with full JD after today; ~2–5k new per day; a daily run fetches only that day's new JDs. Whatever the finder is, it must run on the day's new rows in minutes, and be re-runnable over the whole corpus when rules change (reasons stored per row make that auditable).
- Rules alone got the aggregator sweep to "few worth opening"; what the user does by hand on top is semantic (shape of role, level, lane, disqualifiers buried in the JD). Candidate layering: (1) SQL/rule pass on title + structured fields (cheap, everything), (2) JD-text rules (clearance, assessment gate, platform-gated, plant-floor, travel %, reports), (3) an LLM pass only on what survives (hundreds/day, not thousands) scoring against the memory ground truth, writing `screen_score` + reasons, (4) a daily shortlist view / markdown. Local Gemma (jd_bucketize) or Claude for step 3 — cost/latency is the decision.
- Keep personal rules out of the public repo: the profile split (`profile.py` = structure, `profile_local.py` = the user's numbers/places) is the pattern to extend; the LLM rubric would need the same split.

## Pending / next session
- [x] Liberty Mutual registry row fixed 09-15 ~10:45.
- [ ] **Confirm the backfill chain and Amentum ingest finished**, then run the coverage query above.
- [x] Pushed 09-15 ~11:10 (the user authorized: "after you commit you can push").
- [ ] **Screen engine / job finding:** see the NEXT SESSION brief above — brainstorm first, then build.
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
