# Session Status — Jobsearch

_Last updated: 2026-09-15 13:35 EDT (Claude Code / Opus on Vostro). Overwrite at the end of each session; git history is the changelog._

## Active Sprint
@/docs/SPRINT_PLAN.md — **Phase 1 built and committed locally (not pushed). Next: Fable audits Phase 1 against §11, then Phase 2 (labels + TF-IDF/LR).** Personal values live in the vault's `Tools/Finder_Build_Personal_Appendix.md` and gitignored `backend/profile_local.py`.

**Phase 2 does not need to wait for the live DB.** Labels come from the vault; training reads `vw_label_set` and writes `label_docs` / `models`. Use the scratch copy **`db/finder_scratch.duckdb`** (on E:, gitignored; copied from the live DB at 12:30, 77,777 active / 69,618 JDs, already carries Phase 1 screens under an older rules version, so `finder.py screen` re-screens it). Installing scikit-learn etc. into `.venv` is safe while the backfill runs (that process has its imports loaded; the queued Amentum ingest runs `--no-screen`). Validate the model on the live DB once it is free. Keep large scratch files off C: (`/tmp` is on the C:-backed WSL disk).

## ⚠️ Running right now (check first)

| Stage | State at 12:54 EDT |
|---|---|
| Workday all-titles JD backfill (`output/run_backfill_day.sh`, stage 3) | **Running.** CVS Health 10,800/15,943, ~60 JDs/min now (slower than the morning), so `=== DONE` ≈ 14:20. |
| Amentum ingest | Queued behind `=== DONE`. **The waiter was replaced at 12:32** by `output/after_backfill_amentum_v2.sh` (same command plus `--no-screen`), because the new default finder stage would otherwise have screened the live DB and written a Jobs_Found file into the vault during an ingest. Logs append to `output/amentum_ingest_20260915.log`. |

Check: `grep '^===' output/backfill_20260915_day.log; tail -3 output/amentum_ingest_20260915.log; ps -eo pid,etime,args | grep -E '[a]fter_backfill|[s]weep_ats.py'`

**After both finish, first live finder run:** `.venv/bin/python finder.py rescreen-all` (≈3.5 min on local disk; slower on the external drive), then `finder.py sync`, then `finder.py report` when you want a file. From then on `sweep_ats.py` runs the finder stage itself; `--no-screen` / `--no-report` skip it.

## Phase 1 — what was built
- **`backend/finder/`**: `version.py` (rules_version hash over RULES_CODE_VERSION + every profile constant, sets/dicts sorted), `rules.py` (row→Listing, JD rules: travel, direct reports, domain tenure, discipline, corridor, assessment gate, hours cap, sales ops, tier-3 coding test; `screen_row`; rule points), `pipeline.py` (rescreen predicate, streamed batches, `combine`, `daily`), `tracker_sync.py` (tracker parser + exact/fuzzy match + tracker decisions), `report.py` (Jobs_Found writer per §7, `surfaced` bookkeeping, snapshots, `parse_decisions`, `read_back`).
- **`finder.py`** CLI: `screen`, `rescreen-all`, `report`, `mark`, `sync`, `shortlist` (Phase 2–4 subcommands not added yet). Global `--db` and `--vault`.
- **Schema v3** (`store.py`): screens, tracker, decisions, embeddings, label_docs, models, readback_log, **surfaced** (§4.5); views vw_screen_latest, vw_decisions, vw_shortlist, vw_label_set; macro vw_scored_new(days). `schema_info` bumps 2→3 on open.
- **Sweep integration:** `run(screen=True, report=True, llm_top=0, full_screen=False)`; flags `--no-screen`, `--no-report`, `--llm-top`, `--full-screen`. Finder imported lazily; a finder exception is logged and the run log is still written.
- **Profile split:** public constants per §5 in `profile.py` (+ `CODING_TEST_TERMS`, `SALES_OPS_PATTERN`); neutral example values in `profile_local.example.py`; appendix values in gitignored `profile_local.py`. `.gitignore` gains db/models, db/snapshots, rubric_local.py. `.env.template`, `requirements.txt`, CLAUDE.md updated.
- **Tests:** 44 passing (19 existing + 25 in `tests/test_finder.py`, all on the neutral example profile).

## Deviations from the spec (for the Fable audit)
1. **Card-level discipline test superseded on full JDs.** `screen.py` §4 matches substrings ("implant" → "plant") and was written for 500-char snippets; `rules.screen_row` drops its three discipline outputs and uses `discipline_rule` (word-bounded, plural-tolerant, lane counterweight) instead. `sweep.py` behaviour is unchanged.
2. **Travel span reason uses `B >= 2·M`** (spec says `>`), so the appendix example "20-50%" with a 25% limit is a reason, matching "doubles the limit".
3. **`REQUIRED_HEADINGS` adds** `requirements|qualifications|what you have|what you bring`; `PREFERRED_HEADINGS` adds `sets you apart` (USAA's JD uses "What you have:" / "What sets you apart:"). Heading = a line ≤60 chars, ≤6 words, no final period.
4. **`sales_ops_rule` pattern** is `SALES_OPS_PATTERN`: "pipeline" only as sales/revenue/deal/opportunity pipeline or pipeline management/generation/coverage; CRO only uppercase. The literal spec list would have rejected data-pipeline and pharma-CRO roles.
5. **`hours_cap_rule`:** bare "part-time" counts only in the title, `employment_type = part_time`, or "this/a part-time role/position…". The literal regex flagged 196 tiered rows from benefits boilerplate (incl. the Verizon row via "part-timers"); now 3. Hourly pay is cleared only when the pay is hourly.
6. **`direct_reports_rule`** also reads "team of N" / "staff of N" with the number after.
7. **Tier 3 + assessment gate** is made meaningful with `CODING_TEST_TERMS` (HackerRank, Codility, coding assessment, take-home…) → reason on tier 3 only (memory: data lane only without a coding-test gate).
8. **`is_commutable`** is unchanged in code (hybrid flag alone was already not commutable); docstring states it. The `$…K ask` flag in `screen.py` now reads `P.COMP_ASK` instead of a hard-coded figure (output identical).
9. **Writes** use one JSON string per batch expanded with `json_transform` into a temp table; reads stream from a second cursor. Binding Python lists as DuckDB params cost ~0.8 ms per element (500-row batch: 3.6 s to bind vs 0.01 s to insert/update) — the first full screen was >10 min; now 209 s.
10. **Place matching (13:35, user request):** `screen.place_matches` matches places as whole words per location segment (split on `;` / `|`); an entry `"name, st"` requires that US state in the same segment (uppercase code or full name; "west virginia" is never VA; `d.c.` = DC). `is_commutable` and `corridor_rule` both use it; `profile_local` pins every ambiguous place and leaves only names unique to the area unpinned. On the scratch corpus: 15,362 distinct location strings, old substring matches 339 → 273 now; dropped are Fredericksburg VA, Arlington TX/MA, Leesburg FL, Clarksburg WV, New Brunswick, Frederick CO, Vienna (Austria), Rockville IN, and similar; added are only Washington D.C. forms the old strings missed. Corridor matches outside Maryland: none. RULES_CODE_VERSION 2026-09-15.3.
11. `write_jobs_found` has `table_cap=150`; `report` CLI adds `--block-min-band` and `--since-hours`; `vw_shortlist` joins `SELECT DISTINCT matched_posting_id FROM tracker`.
12. vault_dir may be the vault root (as `.env` has it) or the Job_Search folder; `tracker_sync.job_search_dir` resolves both. (Note: the old `sweep.py` assumes the Job_Search folder, so its tracker dedup is silently off with the current `.env`.)

## §11 acceptance — results (scratch DB, copied 12:30 while the backfill was still writing: 77,777 active, 69,618 with a JD)
- [x] `pytest -q`: 44 passed at the Phase 1 commit; 46 after the place fix.
- [~] `finder.py screen --full`: **209 s** (< 10 min ✅) on local disk. Verdicts **candidate 73 / review 191 / reject 77,513** — candidate+review is **264, not the low thousands** the spec expected. Only 1,184 active rows have a tier at all (function hit in the title); of those, 764 reasons are "not remote and outside the commute area".
- [~] `finder.py report`: parses cleanly (no stray headings, blank lines around every `---`, `# Company:` = `**Fit` = blocks). **Default bar gives 0 blocks**: rules-only `rule_score` tops out at 65 by construction (tier1 30 + extra hits 10 + senior 5 + remote 10 + comp 10), so nothing reaches `strong` (70) until Phase 2 adds `fit`. Scores seen: max 55; bands partial 2, weak 74. With `--block-min-band weak`: 15 blocks, 15 summary rows, 200 passed rows.
- [~] `finder.py sync`: **336 tracker rows, 56 matched (fuzzy), 0 exact** (no Posting ID column yet) — below the spec's >100. Of the 280 unmatched, 151 are employers not in the ATS registry; the other 129 have the employer but a genuinely different req (closest Jaccard ≤ 0.57, e.g. "Program Manager, Operational Excellence" vs "Program Manager"). Threshold left at 0.6 on purpose. Exact matches arrive once the tracker carries Posting IDs (Phase 5).
- [x] `JOBSEARCH_VAULT_DIR=<scratch vault> sweep_ats.py --skip-sweep --detail-budget 0 --db <scratch>`: tracker sync 6.2 s → read-back 0 → screen 0 rows (already current) → Jobs_Found written → 6 snapshot files → 10.3 s total. `--no-screen` runs with no finder output. sklearn is not installed in `.venv`, so every run above proves the no-sklearn path; a test also asserts no optional module is imported.
- [x] Personal-pattern scan empty; `git status` shows no db/models, db/snapshots, rubric_local.py, profile_local.py.

## §11 eyeball (scratch DB, rules 2dc5f061d008 · model none)
Pay figures in comp flags are redacted as `<ask>`/`<top>` here (public repo).

| Expectation | Result |
|---|---|
| Henry Schein R134977 Sr Mgr AI Transformation & Process Excellence: tier 1, top 20 | ✅ **tier 1, rank 2** of vw_shortlist, score 50, review (flag: `<ask> sits above the <top> top`). |
| PFG Global Process Owner Director: tier 1 | ⚠️ **Not in the corpus** (PFG is on BrassRing, no adapter). Other GPO titles: QTS "GPO - Capacity Strategy & Planning" tier 1 rank 7 (flag: plant vocabulary "utilities"); QTS "GPO - Capital Delivery" tier 1; Agilent "HR Operations - GPO" tier 1 reject on location. |
| QIAGEN / Lonza / Kite corridor plant roles: reject | ⚠️ **None of the three employers is in the corpus.** Nearest case: Agilent "Process Engineer - Advanced" (Frederick, **Colorado**) rejects on `different discipline (plant/industrial: manufacturing)` + `corridor manufacturing (required: chemical)` — the corridor rule matched a Colorado Frederick (**fixed 13:35**: places pin their state; the Agilent row still rejects on discipline). Rockville Guidehouse/M&T rows are review, not plant. |
| Equinix Dir Business Process Excellence: sales-ops reason only if GTM/CRO in Required | ⚠️ **Not in the corpus.** Corpus-wide among tiered rows: 44 `sales/revenue ops scope` reasons, 16 vocabulary flags. |
| USAA "10+ years banking" row: domain-tenure flag, not reject | ⚠️ **No such JD.** USAA "Bank Business Process Consultant Lead" (San Antonio) is **candidate**, score 40; its only years line is "8 years of experience in business process consultation…", no banking term, so no flag is correct. A second copy of that req rejects on location. 34 domain-tenure flags corpus-wide (never a reason), e.g. Centene "Director, Provider Data Process Owner" `domain-tenure gate (insurance, 7 yrs)`. |
| Verizon CX Transformation & Change Manager: not comp-rejected | ✅ **Not comp-rejected** (band top above the floor). ⚠️ It **is rejected on location**: Rolling Meadows IL / Temple Terrace FL, workplace_type NULL, so not remote and not commutable — consistent with the 09-14 manual pass on the same row. |
| Crossover: reject `assessment-gated` | ⚠️ **Not in the corpus.** The rule fires elsewhere: SAIC (cognitive assessment), GE Vernova x2 (aptitude test). |
| NFCU Manager II BPO (closed): in history, never in shortlist | ⚠️ **Not in the corpus** (NFCU's 167 Oracle rows hold no business-process title). vw_shortlist filters `status = 'active'` and a closed row cannot appear (tested). |

Top of vw_shortlist: 55 State Street "Global Operational Excellence Lead" (T1) · 50 Henry Schein (T1) · 45 M&T "Senior Organizational Change Manager" · 45 Wells Fargo "…Operational Excellence" (T1) · 40 ServiceNow, Booz Allen, USAA BPC Lead, Centene, Amgen, Included Health, QTS GPO (T1), McKesson.

Eyeball SQL (run with `duckdb.connect(<scratch>)`; the full script lives in the session scratchpad, re-create from these):
```sql
SELECT s.verdict, count(*) FROM vw_screen_latest s JOIN postings p USING (posting_id) WHERE p.status = 'active' GROUP BY 1;
SELECT s.band, s.tier, count(*) FROM vw_screen_latest s JOIN postings p USING (posting_id) WHERE p.status = 'active' GROUP BY 1, 2;
SELECT v.rank, v.final_score, v.tier, v.verdict, v.flags FROM (SELECT row_number() OVER (ORDER BY final_score DESC, first_seen_at DESC) AS rank, * FROM vw_shortlist) v
  JOIN postings p USING (posting_id) WHERE v.employer ILIKE 'henry schein%' AND p.url LIKE '%R134977%';
SELECT p.employer, p.title, s.verdict, s.tier, s.final_score, s.reasons, s.flags FROM vw_screen_latest s JOIN postings p USING (posting_id) WHERE p.title ILIKE '%global process owner%';
SELECT p.employer, p.title, p.location_primary, s.verdict, s.reasons FROM vw_screen_latest s JOIN postings p USING (posting_id)
  WHERE p.status = 'active' AND s.tier IS NOT NULL
    AND regexp_matches(coalesce(p.location_primary,'') || ' ' || coalesce(p.locations,''), 'germantown|walkersville|frederick|gaithersburg|rockville|clarksburg|urbana', 'i');
SELECT count(*) FROM postings WHERE regexp_matches(employer, 'equinix|crossover|qiagen|lonza|kite|performance food', 'i');   -- 0
SELECT p.title, s.verdict, s.tier, s.final_score, s.reasons, s.flags FROM vw_screen_latest s JOIN postings p USING (posting_id) WHERE p.employer ILIKE 'usaa%' AND s.tier IN (1, 2);
SELECT p.location_primary, p.locations, p.workplace_type, s.verdict, s.reasons, s.flags FROM vw_screen_latest s JOIN postings p USING (posting_id)
  WHERE p.employer ILIKE 'verizon%' AND p.title ILIKE '%cx transformation%';
SELECT p.employer, p.title, s.reasons FROM vw_screen_latest s JOIN postings p USING (posting_id) WHERE s.reasons::VARCHAR LIKE '%assessment-gated%';
SELECT split_part(split_part(r, ' (', 1), ':', 1) AS reason, count(*) FROM (SELECT unnest(from_json(s.reasons, '["VARCHAR"]')) AS r
  FROM vw_screen_latest s JOIN postings p USING (posting_id) WHERE p.status = 'active' AND s.tier IS NOT NULL) GROUP BY 1 ORDER BY 2 DESC;
SELECT match_kind, count(*) FROM tracker GROUP BY 1;
```

## Open questions / decisions for the user or the auditor
- **No `strong` blocks in Phase 1** (rule-only max 65). Accept until Phase 2 adds fit, or run `report --block-min-band weak` meanwhile? The daily sweep report uses the default bar.
- **Funnel is narrow** (264 non-reject): the title gate (TITLE_FUNCTION_TERMS) decides tier; 76,593 active rows have no function term in the title. Widening is a profile change, not code.
- ~~Frederick, Colorado / Fredericksburg matching~~ — fixed 13:35 (state-pinned places). `vw_dmv_or_remote_active` in `store.py` is still a coarse city regex (unchanged; it is a browsing view, not a rule).
- **Faith flag text in `screen.py`** still hard-codes a comp range (pre-existing; left alone because `sweep.py` output must not change).
- **Live DB on the external drive:** the 209 s figure is on local disk. Expect the first `rescreen-all` on E: to be slower (one commit per 500 rows; the UPDATE touches `postings`); the daily path screens only new/changed rows.

## Pending (carried)
- [ ] Confirm the backfill + Amentum finished; run the coverage query (`SELECT platform, count(*) FILTER (WHERE description_text IS NOT NULL), count(*) FROM vw_active GROUP BY 1`), then the first live `finder.py rescreen-all` + `sync`.
- [ ] Normal full sweep afterwards picks up Microsoft / Omnicell / Liberty Mutual / Logos.
- [ ] Daily schedule (cron / Task Scheduler).
- [ ] Long tail adapters: iCIMS, Dayforce, Radancy (UHG, L3Harris), BrassRing (PFG).
- [ ] Registry gaps: 7 "generic slug, VERIFY" rows; ProSidian SmartRecruiters id.
- [ ] Aggregator keys missing from Vostro `.env`; `sweep.py` JOBSEARCH_VAULT_DIR shape mismatch (above).
- [ ] Cleanup: `db/jobsearch.duckdb.v1-backup-20260915`, the history bundle, `output/after_backfill_amentum.sh` (superseded).

## Run
```bash
.venv/bin/python sweep_ats.py                                   # sweep + JDs + finder stage (tracker sync, screen, report, snapshots)
.venv/bin/python sweep_ats.py --no-screen                       # sweep only
.venv/bin/python finder.py rescreen-all                         # after a profile/rules change
.venv/bin/python finder.py shortlist --days 7 --n 30
.venv/bin/python finder.py mark <posting_id|url|"employer|title"> pass --reason "..."
.venv/bin/python -m pytest -q
```
