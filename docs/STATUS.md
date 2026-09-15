# Session Status — Jobsearch

_Last updated: 2026-09-15 14:00 EDT (Claude Code / Opus on Vostro). Overwrite at the end of each session; git history is the changelog._

## Active Sprint
@/docs/SPRINT_PLAN.md — **Phase 2 (labels + TF-IDF/LR) built and committed locally (not pushed). Next: Fable audits Phase 2 against §11, then Phase 3 (embeddings).** Phase 1 was committed earlier the same day. Personal values live in the vault's `Tools/Finder_Build_Personal_Appendix.md` and gitignored `backend/profile_local.py`.

All Phase 2 numbers below are from the scratch copy **`db/finder_scratch.duckdb`** (E:, gitignored; 77,777 active / ~69.6k with a JD). The live DB was still locked by the backfill at 13:40. It now carries `label_docs`, a trained model `12bd55424307` (`db/models/12bd55424307.joblib`), and screens under rules `f1451d3ad1e9` · model `12bd55424307`.

## ⚠️ Running right now (check first)
At 13:40 EDT the Workday all-titles JD backfill (`output/run_backfill_day.sh`, stage 3, PID 105892, running 3 h 25 m) was still going, with the Amentum waiter `output/after_backfill_amentum_v2.sh` (`--no-screen`) queued behind `=== DONE`.

Check: `grep '^===' output/backfill_20260915_day.log; tail -3 output/amentum_ingest_20260915.log; ps -eo pid,etime,args | grep -E '[a]fter_backfill|[s]weep_ats.py'`

**After both finish, first live run:** `finder.py labels --report` → `finder.py train --report` → `finder.py rescreen-all` (≈5.5 min with the model on local disk; slower on E:) → `finder.py sync` → `finder.py report` when a file is wanted. From then on `sweep_ats.py` loads the newest model itself. A new model version makes every active row due, so the first sweep after a retrain does a full rescreen.

## Phase 2 — what was built
- **`backend/finder/labels.py`**: `strip_boilerplate`, `jd_section`, `load_applications` (frontmatter status → label; JD ≥ 800 chars), `load_jobs_found_escalated` (weight 0.7, deduped against applications and across files), `load_jobs_found_passed` (label 0, text from a matched posting), `PostingIndex` / `match_to_postings` (exact URL → employer req_id inside the URL → company keys + `similar_title`), `pseudo_negatives` (deterministic `hash(posting_id || seed)` order, current `screen_row` rejects on off-function / off-lane title), `sync_labels` (rebuilds the four label sources in one transaction), `label_counts`.
- **`backend/finder/features.py`**: `doc_text` (title twice + boilerplate-stripped JD), `training_set` (vw_label_set deduped), `cross_validate` (StratifiedKFold, out-of-fold probs, fold-mean AUC + precision@20), `train` (joblib to `db/models/<version>.joblib`, `models` row, `notes` JSON carries `fit_weight` / warnings / params), `hard_negatives`, `load_latest` (None when no model, file gone, or sklearn missing), `predict`, `predict_with_terms` (one transform per batch; tf-idf × coef top positives), `top_terms`, `signal_report`.
- **`pipeline.py`**: `screen(model=…)` fills `fit_prob` + `top_terms` (only rows with JD text), `model_version` = the model's version, `combine` gets `fit_weight` from the model; `daily(use_model=True)` loads the newest model and marks the Model stage on in the report.
- **`finder.py`**: `labels [--report] [--pseudo N] [--seed N]`, `train [--cv 5] [--C 4.0] [--report]` (always prints the hard-negative list); `screen --no-model` and `rescreen-all --no-model` now work; `report` stamps the latest screens' model version.
- scikit-learn 1.9.1, numpy 2.5.3, scipy 1.18.1, joblib 1.6.0 installed in `.venv` (requirements.txt keeps them commented as optional). CLAUDE.md repo map updated.
- **Tests: 53 passing** (46 + 7 new: boilerplate/jd_section, passed-reason classes, vault loaders incl. pipeline-file skip, pseudo-negatives + sync_labels rebuild, training-set dedupe, train/predict/top_terms/load_latest, screen with a model).

## Phase 2 deviations (for the Fable audit)
1. **Pipeline-written Jobs_Found files are not label sources** (`# Jobs Found — ATS pipeline` marker). Their blocks and passed rows are the rules' own output; training on them would teach the model to echo the rules.
2. **Passed rows are filtered by reason** (`classify_passed_reason`): `stale` (closed / expired / already tracked / duplicate) and `logistics` (location or pay only, with no fit word) are skipped. On the vault: 101 logistics, 44 stale, 24 duplicate skipped; 356 fit-reason rows kept (label 0, text only when matched: 20). A location-only pass (e.g. the Verizon CX row) is a good function in a bad place, not a text negative.
3. **Escalated blocks use the same 800-char minimum** as applications (text NULL below it, so they count but do not train). Blocks end at `---`, the next `# Company:`, an H1, or a file-level `## ` section (older hand-made files run blocks back to back; `## Description:` stays inside a block).
4. **Dedupe in `training_set`**, priority application > decision > escalated > passed > pseudo: one doc per posting_id; a decision row is dropped when a vault doc with matching company + similar title exists (the tracker decisions otherwise double-count applications with the ATS copy of the same JD), and its posting_id stays reserved so no lower source relabels it. Pseudo-negatives exclude every application/escalated positive and every `build` decision posting.
5. **Applications also carry a posting match** (Apply URL or company + title): 52 of 297 matched; used only for dedupe and signal AUCs.
6. `sync_labels` **replaces** the four vault/pseudo sources each run (DELETE + INSERT in one transaction) rather than upserting, so a deleted folder disappears.
7. `train` also reports **AUC vs non-pseudo negatives only** and positives' mean fit held-out vs in-sample, because pseudo-negatives are easy and inflate the headline AUC.
8. `top_terms` are computed for every row with a JD (rejects included), so a rule reject with a high fit is visible for auditing the title gate.

## §11 Phase 2 acceptance — results (scratch DB)
- [x] `pytest -q`: **53 passed**.
- [~] `finder.py labels --report`: **395 positives with text** (≥ 250 ✅: application 282, decision 45, escalated 68) · **35 non-pseudo negatives with text** (< 150: application 15, passed 20) → **warning path exercised**: `fit_weight` 0.15. 1,500 pseudo-negatives. After dedupe: 1,880 training docs (347 pos / 1,533 neg, 33 non-pseudo neg). 20 s.
- [x] `finder.py train --report`: **5-fold AUC 0.985** (≥ 0.85 ✅) · precision@20 0.960 · **positives' mean fit 0.80 held-out** / 0.89 in-sample (> 0.7 ✅) · confusion@0.5 tp 321 / fp 65 / fn 26 / tn 1,468 · AUC vs non-pseudo negatives only **0.741** (the honest number: 33 real negatives). 43 s.
- [x] Hard-negative list printed and plausible: top label-0 docs are the user's own near-miss passes (McKesson Sr Dir Business Modernization 0.98, RGP Finance Transformation PM 0.94, Peraton BPI Lead 0.93, Sysco AI Transformation Office PMO 0.91, CareFirst Business Readiness 0.87, Guidehouse Internal Control & BT 0.83), one NFCU passed row (comp/level) 0.96, and pseudo-negatives that really are adjacent (GE Vernova Plant Leader 0.87, Agilent AVP Manufacturing 0.84, Amgen Clinical System Ops Sr Dir 0.75).
- [x] `top_terms` in the Fit stanza read sensibly, e.g. `**Fit: ~46%.** rule 30 · fit 0.87 · top terms: transformation, change management, lean, strategic, operational, change · tier 2`; data-lane rows show `analytics, business intelligence, data, bi`.
- [x] `finder.py rescreen-all` with the model: **327 s** (rules-only was 209 s). Verdicts candidate 73 / review 193 / reject 77,511 (±2 vs Phase 1: the rules version changed with the 13:50 place fix).
- [x] `sweep_ats.py --skip-sweep --detail-budget 0 --db <scratch>` with a scratch vault: model loaded, screen 0 rows (current), report + 6 snapshots. No-sklearn path: with `sys.modules['sklearn'] = None` and a `models` row present, `load_latest` logs "rules only" and screens write model `none`; `test_finder_import_pulls_no_optional_dependencies` still passes.
- [x] Personal-pattern scan empty; `db/models/`, `db/snapshots/` untracked.

## §11 eyeball — Phase 2 (scratch DB, rules f1451d3ad1e9 · model 12bd55424307)
| Check | Result |
|---|---|
| Henry Schein R134977 | ✅ **rank 1** of vw_shortlist, final **62** partial, tier 1, rule 50, **fit 0.93**, terms transformation, strategic, sigma, lean, improvement, change management. |
| Top of vw_shortlist | 62 Henry Schein (T1, fit .93) · 58 M&T Sr Organizational Change Mgr (fit .94) · 52 / 50 QTS GPO x2 (T1, fit .82 / .92) · 50 Amgen AVP AI&D Scaled Ops & Transformation (fit .78) · 48 State Street Global OpEx Lead (rule 55 but **fit .28**, dropped from 1st to 6th) · 47 Angi Principal Analytics Eng (T3) · 46 GE Vernova Transformation Leader · 44 McKesson Dir IT OCM, Centene Dir Provider Data Process Owner, Perficient Dir OCM. |
| GPO titles | QTS x2 review (fit .82/.92); Agilent HR Ops GPO reject on location (fit .78); McKesson "GPO Strategy" (purchasing GPO) reject, fit .18 ✅. |
| USAA | BPC Lead candidate, final 38, fit .32; BPO Intern reject, fit .15. |
| Verizon CX Transformation | reject on location (unchanged), fit .26. |
| fit_prob by verdict (active) | reject avg .114 (2,129 ≥ 0.5) · review avg .27 (35 ≥ 0.5) · candidate avg .416 (27 ≥ 0.5). |
| Label rows' mean fit in screens | application+ .604 (n 50) · decision .572 (45) · escalated .717 (11) · passed .299 (20) · application− .176 (2) · pseudo .097 (1,500; in-sample). |
| Bands / blocks | partial 10, weak 69, none 77,698. **Default bar still gives 0 blocks** (max final 62). With the low-data fit weight 0.15 the blend is `(0.40·rule + 0.15·fit·100) / 0.55`, so strong (70) needs rule ≥ ~57 and fit ≈ 1; rule tops out at 65. `--block-min-band weak`: 15 blocks. |
| Signal AUCs (`train --report`, labeled rows with a screen) | rule_score .844 all / .448 non-pseudo · fit (held-out) .982 / .836 · blend .602 / .516 (a rule reject forces final 0, and most labeled postings reject on location). |
| High fit, no tier (title gate misses) | Honeywell "Director Operational Ex" (truncated title) .96 · Phil, Inc "Director of Business Operations, Client Optimization" .95 (off-function title only) · Amgen "Strategic Planning & Operations Manager" .99 · Novartis "Assoc Dir, Governance & Operations" .94 — evidence for the funnel question below. |

Eyeball SQL (Phase 2 additions; Phase 1 queries are in git history of this file):
```sql
SELECT rules_version, model_version, count(*) FROM vw_screen_latest GROUP BY 1, 2;
SELECT s.verdict, count(fit_prob), round(avg(fit_prob), 3), count(*) FILTER (WHERE fit_prob >= 0.5)
  FROM vw_screen_latest s JOIN postings p USING (posting_id) WHERE p.status = 'active' GROUP BY 1;
SELECT final_score, band, tier, rule_score, round(fit_prob, 2), employer, title, top_terms FROM vw_shortlist LIMIT 15;
SELECT v.rank, v.final_score, v.band, v.tier, v.rule_score, round(v.fit_prob, 2), v.top_terms
  FROM (SELECT row_number() OVER (ORDER BY final_score DESC, first_seen_at DESC) AS rank, * FROM vw_shortlist) v
  JOIN postings p USING (posting_id) WHERE v.employer ILIKE 'henry schein%' AND p.url LIKE '%R134977%';
SELECT p.employer, p.title, s.verdict, s.tier, s.final_score, round(s.fit_prob, 2) FROM vw_screen_latest s JOIN postings p USING (posting_id)
  WHERE p.title ILIKE '%global process owner%' OR p.title ILIKE '%gpo%';
SELECT round(s.fit_prob, 2), p.employer, p.title, s.reasons FROM vw_screen_latest s JOIN postings p USING (posting_id)
  WHERE p.status = 'active' AND s.tier IS NULL ORDER BY s.fit_prob DESC NULLS LAST LIMIT 12;
SELECT count(*) FILTER (WHERE band IN ('very_strong', 'strong')), count(*) FILTER (WHERE final_score >= 50), max(final_score) FROM vw_shortlist;
SELECT l.source, l.label, count(*), round(avg(s.fit_prob), 3) FROM vw_label_set l JOIN vw_screen_latest s USING (posting_id) GROUP BY 1, 2;
```

## Open questions / decisions for the user or the auditor
- **Real negatives are the bottleneck** (35 with text). The fastest lift is `finder.py mark <id> pass --reason …` on shortlist rows the user would not build, or passing rows in the next Jobs_Found Decision column; each one with a JD becomes a label. At 150 the fit weight returns to 0.35 and strong blocks become reachable.
- **No `strong` blocks yet** (max 62). Options: accept until labels grow; run `report --block-min-band partial` meanwhile; or revisit `LOW_DATA_FIT_WEIGHT` (0.15 is the spec value).
- **Title gate vs model:** 2,129 active rule rejects have fit ≥ 0.5; many are `off-function title` only. Widening TITLE_FUNCTION_TERMS (e.g. "operational ex", "business operations", "operations planning") is a profile change; alternatively a future rule could downgrade `off-function title` to a flag when fit ≥ ~0.9.
- **Blend AUC below fit alone** because hard rejects score 0; expected by design, but the weights in §6 were not tuned (Phase 2 only reports).
- Faith flag text in `screen.py` still hard-codes a comp range (pre-existing). `vw_dmv_or_remote_active` is still a coarse regex.
- Surfacing: the Phase 1 report runs on scratch recorded `surfaced` rows, so Henry Schein et al. are excluded from new blocks there for 14 days (scratch only).

## Phase 1 — what was built (carried for the audit)
- **`backend/finder/`**: `version.py` (rules_version hash over RULES_CODE_VERSION + every profile constant, sets/dicts sorted), `rules.py` (row→Listing, JD rules: travel, direct reports, domain tenure, discipline, corridor, assessment gate, hours cap, sales ops, tier-3 coding test; `screen_row`; rule points), `pipeline.py` (rescreen predicate, streamed batches, `combine`, `daily`), `tracker_sync.py` (tracker parser + exact/fuzzy match + tracker decisions), `report.py` (Jobs_Found writer per §7, `surfaced` bookkeeping, snapshots, `parse_decisions`, `read_back`).
- **`finder.py`** CLI: `screen`, `rescreen-all`, `report`, `mark`, `sync`, `shortlist` (Phase 2–4 subcommands not added yet). Global `--db` and `--vault`.
- **Schema v3** (`store.py`): screens, tracker, decisions, embeddings, label_docs, models, readback_log, **surfaced** (§4.5); views vw_screen_latest, vw_decisions, vw_shortlist, vw_label_set; macro vw_scored_new(days). `schema_info` bumps 2→3 on open.
- **Sweep integration:** `run(screen=True, report=True, llm_top=0, full_screen=False)`; flags `--no-screen`, `--no-report`, `--llm-top`, `--full-screen`. Finder imported lazily; a finder exception is logged and the run log is still written.
- **Profile split:** public constants per §5 in `profile.py` (+ `CODING_TEST_TERMS`, `SALES_OPS_PATTERN`); neutral example values in `profile_local.example.py`; appendix values in gitignored `profile_local.py`. `.gitignore` gains db/models, db/snapshots, rubric_local.py. `.env.template`, `requirements.txt`, CLAUDE.md updated.
- **Tests:** 44 passing (19 existing + 25 in `tests/test_finder.py`, all on the neutral example profile).

## Phase 1 deviations (for the Fable audit)
1. **Card-level discipline test superseded on full JDs.** `screen.py` §4 matches substrings ("implant" → "plant") and was written for 500-char snippets; `rules.screen_row` drops its three discipline outputs and uses `discipline_rule` (word-bounded, plural-tolerant, lane counterweight) instead. `sweep.py` behaviour is unchanged.
2. **Travel span reason uses `B >= 2·M`** (spec says `>`), so the appendix example "20-50%" with a 25% limit is a reason, matching "doubles the limit".
3. **`REQUIRED_HEADINGS` adds** `requirements|qualifications|what you have|what you bring`; `PREFERRED_HEADINGS` adds `sets you apart` (USAA's JD uses "What you have:" / "What sets you apart:"). Heading = a line ≤60 chars, ≤6 words, no final period.
4. **`sales_ops_rule` pattern** is `SALES_OPS_PATTERN`: "pipeline" only as sales/revenue/deal/opportunity pipeline or pipeline management/generation/coverage; CRO only uppercase. The literal spec list would have rejected data-pipeline and pharma-CRO roles.
5. **`hours_cap_rule`:** bare "part-time" counts only in the title, `employment_type = part_time`, or "this/a part-time role/position…". The literal regex flagged 196 tiered rows from benefits boilerplate (incl. the Verizon row via "part-timers"); now 3. Hourly pay is cleared only when the pay is hourly.
6. **`direct_reports_rule`** also reads "team of N" / "staff of N" with the number after.
7. **Tier 3 + assessment gate** is made meaningful with `CODING_TEST_TERMS` (HackerRank, Codility, coding assessment, take-home…) → reason on tier 3 only (memory: data lane only without a coding-test gate).
8. **`is_commutable`** is unchanged in code (hybrid flag alone was already not commutable); docstring states it. The `$…K ask` flag in `screen.py` now reads `P.COMP_ASK` instead of a hard-coded figure (output identical).
9. **Writes** use one JSON string per batch expanded with `json_transform` into a temp table; reads stream from a second cursor. Binding Python lists as DuckDB params cost ~0.8 ms per element (500-row batch: 3.6 s to bind vs 0.01 s to insert/update) — the first full screen was >10 min; now 209 s.
10. **Place matching (13:35, user request):** `screen.place_matches` matches places as whole words per location segment (split on `;` / `|`); an entry `"name, st"` requires that US state in the same segment (uppercase code or full name; "west virginia" is never VA; `d.c.` = DC). `is_commutable` and `corridor_rule` both use it; `profile_local` pins every ambiguous place and leaves only names unique to the area unpinned. On the scratch corpus: 15,362 distinct location strings, old substring matches 339 → 279 now (after the `st?` form below); dropped are Fredericksburg VA, Arlington TX/MA, Leesburg FL, Clarksburg WV, New Brunswick, Frederick CO, Vienna (Austria), Rockville IN, and similar; added are only Washington D.C. forms the old strings missed. Corridor matches outside Maryland: none. **`"name, st?"`** (13:50, user request) makes the state optional: a bare name counts, another state never does; used for the area's distinctive names plus Vienna, Rockville and Winchester (a reverse commute). Known gap: a non-US country is not a US state, so "AT, Vienna" (Austria) still matches `vienna, va?`. RULES_CODE_VERSION 2026-09-15.4.
11. `write_jobs_found` has `table_cap=150`; `report` CLI adds `--block-min-band` and `--since-hours`; `vw_shortlist` joins `SELECT DISTINCT matched_posting_id FROM tracker`.
12. vault_dir may be the vault root (as `.env` has it) or the Job_Search folder; `tracker_sync.job_search_dir` resolves both. (Note: the old `sweep.py` assumes the Job_Search folder, so its tracker dedup is silently off with the current `.env`.)

## §11 Phase 1 acceptance — results (scratch DB, copied 12:30 while the backfill was still writing: 77,777 active, 69,618 with a JD)
- [x] `pytest -q`: 44 passed at the Phase 1 commit; 46 after the place fix.
- [~] `finder.py screen --full`: **209 s** (< 10 min ✅) on local disk. Verdicts **candidate 73 / review 191 / reject 77,513** — candidate+review is **264, not the low thousands** the spec expected. Only 1,184 active rows have a tier at all (function hit in the title); of those, 764 reasons are "not remote and outside the commute area".
- [~] `finder.py report`: parses cleanly (no stray headings, blank lines around every `---`, `# Company:` = `**Fit` = blocks). **Default bar gives 0 blocks**: rules-only `rule_score` tops out at 65 by construction (tier1 30 + extra hits 10 + senior 5 + remote 10 + comp 10), so nothing reaches `strong` (70) until Phase 2 adds `fit`. Scores seen: max 55; bands partial 2, weak 74. With `--block-min-band weak`: 15 blocks, 15 summary rows, 200 passed rows.
- [~] `finder.py sync`: **336 tracker rows, 56 matched (fuzzy), 0 exact** (no Posting ID column yet) — below the spec's >100. Of the 280 unmatched, 151 are employers not in the ATS registry; the other 129 have the employer but a genuinely different req (closest Jaccard ≤ 0.57, e.g. "Program Manager, Operational Excellence" vs "Program Manager"). Threshold left at 0.6 on purpose. Exact matches arrive once the tracker carries Posting IDs (Phase 5).
- [x] `JOBSEARCH_VAULT_DIR=<scratch vault> sweep_ats.py --skip-sweep --detail-budget 0 --db <scratch>`: tracker sync 6.2 s → read-back 0 → screen 0 rows (already current) → Jobs_Found written → 6 snapshot files → 10.3 s total. `--no-screen` runs with no finder output. sklearn is not installed in `.venv`, so every run above proves the no-sklearn path; a test also asserts no optional module is imported.
- [x] Personal-pattern scan empty; `git status` shows no db/models, db/snapshots, rubric_local.py, profile_local.py.

## §11 eyeball — Phase 1 (scratch DB, rules 2dc5f061d008 · model none)
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

## Phase 1 open questions (carried)
- **No `strong` blocks in Phase 1** (rule-only max 65). Accept until Phase 2 adds fit, or run `report --block-min-band weak` meanwhile? The daily sweep report uses the default bar.
- **Funnel is narrow** (264 non-reject): the title gate (TITLE_FUNCTION_TERMS) decides tier; 76,593 active rows have no function term in the title. Widening is a profile change, not code.
- ~~Frederick, Colorado / Fredericksburg matching~~ — fixed 13:35 (state-pinned places). `vw_dmv_or_remote_active` in `store.py` is still a coarse city regex (unchanged; it is a browsing view, not a rule).
- **Faith flag text in `screen.py`** still hard-codes a comp range (pre-existing; left alone because `sweep.py` output must not change).
- **Live DB on the external drive:** the 209 s figure is on local disk. Expect the first `rescreen-all` on E: to be slower (one commit per 500 rows; the UPDATE touches `postings`); the daily path screens only new/changed rows.

## Pending (carried)
- [ ] Confirm the backfill + Amentum finished; run the coverage query (`SELECT platform, count(*) FILTER (WHERE description_text IS NOT NULL), count(*) FROM vw_active GROUP BY 1`), then on the live DB: `labels` → `train` → `rescreen-all` → `sync`.
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
.venv/bin/python finder.py rescreen-all                         # after a profile/rules change or a retrain
.venv/bin/python finder.py labels --report                       # rebuild label_docs from the vault
.venv/bin/python finder.py train --report                        # retrain the fit model
.venv/bin/python finder.py shortlist --days 7 --n 30
.venv/bin/python finder.py mark <posting_id|url|"employer|title"> pass --reason "..."
.venv/bin/python -m pytest -q
```
