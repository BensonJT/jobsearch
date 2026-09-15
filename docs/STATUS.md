# Session Status — Jobsearch

_Last updated: 2026-09-15 evening (Claude Code / Opus on Vostro; Phase 3a built and measured). Overwrite at the end of each session; git history is the changelog._

## Active Sprint
@/docs/SPRINT_PLAN.md — **Phase 3a is BUILT (commit `ebcf40c`, local, not pushed) and its §15.7 eyeball FAILED. Do not start 3b or Phase 4.** Coverage is computed, stored and displayed at weight 0, exactly as §16.6 requires, and the gate it describes is what caught the problem: requirement coverage as specified does not separate fits from near misses on this corpus (details below). The next decision is a design one and belongs to the user with Fable: keep absolute cosine bands and change the inputs, or replace the band scheme with a contrast measure. Phases 1 and 2 are unchanged and live.

## The live DB is current
- **First live finder run, 2026-09-15 (the user ran it):** `labels --report` → `train --report` → `rescreen-all` → `sync`. Model **`ec851b252dc3`** (359 pos / 1,500 pseudo-neg, 5-fold AUC 0.983, precision@20 1.000, positives mean fit 0.80 held-out / 0.90 in-sample). Rescreen: **80,276 active rows in 526 s** under rules `a844b0d2d80d` — candidate 276 · review 1,708 · reject 78,292; bands very_strong 78 · strong 544 · partial 1,226 · weak 136. Tracker: 336 rows, 56 fuzzy, 0 exact, 48 decisions added.
- **First live pipeline report:** the run chain had no `report` step, so Claude ran `finder.py report`: vault `Search_Results/Jobs_Found_20260915_1821.md` (15 blocks, 150 summary rows, snapshots refreshed). Auto-synced to the vault.
- Top of that file: Henry Schein R134977 96 · Humana AVP Corp Dev Integration 95 · Amgen AVP AI&D 95 · M&T Sr Org Change Mgr 94 · CVS VP & COO Medical Affairs 93 · USAA HR Integration Principal 93 · Humana Portfolio Enablement Lead 93. The context misfires are still in the top 15 — the problem Phase 3 was built to solve.
- **The live DB is still schema v3 and has no coverage data.** All Phase 3a work ran on `db/finder_scratch.duckdb` (copied from the live file at 18:21, after the report). The first live run with this code will add the coverage tables and bump it to v4 (additive only; `postings` untouched). `rules_version` is unchanged at `a844b0d2d80d`, so the live screens stay valid.

## Phase 3a — what was built (commit `ebcf40c`)
- `backend/finder/evidence.py` — TOML manifest (`evidence.local.toml`, gitignored; `JOBSEARCH_EVIDENCE` overrides), csv / markdown / pdf / html / text loaders, 40–600 char units, kind weights, per-source `skip_headings` / `skip_patterns`, guards loaded but never embedded, `evidence_units` with `FLOAT[384]` vectors.
- `backend/finder/requirements.py` — JD → requirement units with section, group (required / role), weight and class (work / level / logistics / domain); §16.4 years handling; line rejoining for career-site HTML; `splitter_fingerprint()`.
- `backend/finder/embed.py` — bge-small-en-v1.5 loader (sentence-transformers, then fastembed), query instruction on the requirement side, JSON vector writer, `fetchnumpy` reader.
- `backend/finder/coverage.py` — bands on raw cosine with kind weight applied to credit (§16.2), `not_in_record` / `light_in_record` tiers (§16.5), specificity (§16.3), unit cache, `cover()`, and `calibrate()` against hard negatives with blend AUCs and the paired source gap (§16.1).
- `backend/finder/setup_check.py`, schema v4 (`evidence_units`, `requirement_units`, `coverage`, `hard_negatives`, `vw_coverage_latest`, `vw_hard_negatives`, `vw_decisions.reason_code`, coverage columns on `vw_shortlist`), CLI `evidence` / `coverage` / `setup-check`, `mark pass --reason <code>`, coverage stage in `pipeline.daily`, coverage fields in the Fit stanza, `docs/SETUP_CONTEXT.md`, `evidence.example.toml` + `tests/fixtures/evidence/`.
- **Tests: 78 passing** (15 new). Personal-pattern scan empty. `setup-check` passes on this machine.

## Phase 3a results on the scratch DB (1,983 survivors, 2,888 evidence units, evidence `74156dda6991`)
| Acceptance check (§15.7 / §16.9) | Result |
|---|---|
| Henry Schein R134977 covers ≥ 80 | ❌ **53.8** required (5 of 40 strong, 35 partial) |
| Each named misfire ≥ 20 points below it | ❌ CVS VP & COO **50.0** · Novartis AI Foundations **50.0** · Centene Sr Dir Medical Economics **52.0** · Humana Creative Ops **52.5** · Centene VP Medicare **50.0** — all within 4 points |
| Paired vault vs career-site gap < 5 points | ✅ **0.14** points (n = 42) |
| Coverage of all survivors < 15 min | ❌ cold **22 min** (1,330 s; 1,216 s of it first-time embedding) · ✅ warm **132 s** from the unit cache |
| Sweep runs with no embedding library | ✅ `coverage_stage` logs the reason and returns None |
| Hard-negative view populated | ✅ 207 (7 audit + 200 top-fit unlabeled) |
| Calibration report | ✅ printed; see below |
| Specificity spot check | ✅ boilerplate sinks (salary / benefits / "kept confidential" lines 0.26–0.27, 74–223 postings each); unique lines 1.0; median 1.0, p25 0.79 |
| Step 3a at weight 0, both figures in the stanza | ✅ final scores identical before and after coverage |

**Calibration `5a888e545929`** (628 s; 362 positives, 57 with career-site text · 207 hard negatives · 300 pseudo): chose COVER_STRONG **0.74**, COVER_PARTIAL **0.54** (the grid's bottom edge), COVERAGE_REJECT 43.9, COVERAGE_REVIEW 47.9. AUC positives vs hard negatives: coverage_required **0.598** · coverage_role 0.527 · gated 0.590 · fit held-out 0.383 (expected: those negatives are the fit model's own top scorers) · best blend weight 0.9 (i.e. the blend prefers almost no coverage). Sanity AUC vs pseudo-negatives 0.623. Medians: positives 50.29, hard negatives 50.00.

## Why it failed (diagnosis, for the 3b design decision)
1. **The cosines have no dynamic range on this data.** Best-match cosine over sampled survivors: min 0.54 · p25 0.62 · **median 0.65** · p75 0.72 · max 0.84. §16.2 assumed related sentences sit at 0.75–0.90; with bge-small they sit near 0.65 whether or not the requirement is a real match.
2. **So every requirement lands in one band.** Over the survivor set: **93.3 % partial, 5.6 % strong**. Credit therefore ≈ 0.5 × kind weight for nearly every unit, and coverage collapses to a constant: survivor `coverage_required` p05 46.2 · p25 50.0 · **median 50.0** · p75 52.0 · p95 56.6. A 10-point range cannot separate anything.
3. **Calibration could only pick the degenerate corner.** Maximizing a flat AUC surface drove COVER_PARTIAL to the grid's lowest value, which is the "give everything partial credit" solution.
4. **The negatives are not the problem.** Positives separate from audited misfires, the fit model's confident mistakes and random pseudo-negatives at almost the same AUC (0.71 / 0.72 / 0.71 on the subset that has coverage). Coverage is not confusing near misses with fits — it is not ranking anything.
5. **What does work:** the source-invariance fix (0.14-point paired gap), specificity (boilerplate down to 0.26), the evidence pipeline (matches are dominated by `resume_bullets` and `soar_stories`, the achievement-kind sources, exactly as intended), and the unit cache (warm re-cover 132 s).
6. **Symptom worth seeing:** ranking survivors by `coverage_required` puts GitLab "Staff Backend Engineer" (77.0), Guidehouse "Data Platform Lead" (73.0) and "Adobe Commerce Sr. Solutions Architect" (63.7) on top — short, terse requirement lists with few units, where noise dominates.

## Options for 3b (not built; the user decides with Fable)
- **A. Contrast instead of absolute bands.** Score each requirement by how far its best evidence cosine sits above that requirement's own baseline (its median or 90th percentile cosine against the whole evidence store), so the constant offset cancels. Cheapest change, keeps everything else.
- **B. A stronger encoder** (bge-base / bge-large / e5-large) for wider spread, at 3–10× the embedding cost; the unit cache makes a one-off re-embed tolerable but the daily path slows too.
- **C. Keep bands, fix the inputs:** require a minimum `n_required` (the tech-role artifact above), raise the specificity floor so generic lines cannot carry credit, and hand-set thresholds from the observed distribution rather than letting a flat AUC choose them.
- **D. Skip to Phase 4 for the top N** (LLM review reads context directly) and keep coverage as a reported figure only.

## Deviations from the spec (for the Fable audit)
## Phase 3a deviations (for the Fable audit)
1. **PDF text without `-layout`.** `pdftotext -layout` interleaves the LinkedIn export's two columns on one line; plain `pdftotext` gives reading order (sidebar, then main). §15.1 said `-layout`.
2. **No pyarrow.** Vectors are written as one JSON payload (`json_transform` → `FLOAT[]` → `FLOAT[384]`) and read per row with `fetchnumpy()` + `np.stack` (5k vectors: write 0.7 s, read 0.03 s). Binding `?::FLOAT[384]` per row is used only in the cosine test.
3. **Splitter additions to §15.2:** `PERSON_HEADINGS` (skills, knowledge, experience, education, who you are…) count as Required for coverage only (Henry Schein's requirements sit under "SPECIFIC KNOWLEDGE & SKILLS"); `DROP_HEADINGS` for about-us / benefits / pay / EEO; text before the first recognized heading is `intro` at weight 0.5 (role group); an unrecognized Title Case or colon-ended label line is skipped; lines are rejoined when career-site HTML split a sentence around bold spans; employer notices (pay-range statements, scam warnings, career-site pointers) are dropped; any line naming pay is logistics.
4. **Requirement units are embedded uncapped**, then specificity, then the 40-unit cap (§16.3 needs specificity before the cap). Identical unit texts across postings are encoded once (46,374 unique of 64,760 work units on the survivor set).
5. **Specificity reference = every survivor's cached work units**; a posting outside the survivor set (calibration docs) is measured against the same reference with N + 1. Spec is stored on first coverage and recomputed only by `coverage --all`, so it drifts slowly as the survivor set changes.
6. **Coverage table columns** follow §16.3 (two figures + counts per group) instead of §15.3's single `coverage / n_work / n_strong / n_partial`; PK adds `calibration`, so a re-calibration re-scores from the unit cache without re-embedding.
7. **Hard negatives:** `vw_hard_negatives` = `pass` decisions with reason code `function` ∪ table `hard_negatives` (audit ids from `AUDIT_NEGATIVES` + the top-fit unlabeled postings with no function term, rewritten by each calibration). `AUDIT_NEGATIVES` is exempt from `rules_version` (a calibration input), so adding ids never forces a rescreen.
8. **Reason codes** are parsed from the reason text (`function: …`), not a new column: `vw_decisions.reason_code` (existing free-text passes = `other`). `mark pass` refuses a reason that does not start with a code.
9. **Calibration fit AUC uses held-out fit** (a fresh cross-validation with the newest model's parameters); in-sample fit would flatter the fit model against coverage. Pseudo-negatives for the sanity AUC default to 300 (not 1,500) to save embedding time.
10. **Encoder:** sentence-transformers 6.0.1 on CPU torch 2.14 (4 threads), ~50 units/s. fastembed 0.8 (ONNX) was installed and measured slower on this machine (90 s vs 40 s per 2,000 units, vectors within 0.0009), so `auto` picks sentence-transformers. First model load downloads ~130 MB into `~/.cache/huggingface`.
11. Evidence manifest gained `skip_headings` / `skip_patterns` per source (vault documents carry AI-usage notes, coaching notes and negative positioning statements that would otherwise match JD text).

## Pending
- [ ] **Decision: which 3b option (or none).** Phase 4 stays blocked until coverage earns its weight (§16.6).
- [ ] Confirm the `not_in_record` starter list (Power BI, Tableau, Prosci certification, PMP, CSM) and `light_in_record` (AWS, Azure, GCP) in `evidence.local.toml`.
- [ ] Run the live DB through `evidence --rebuild` → `coverage` when 3b lands (cold cost ≈ 25 min; the live corpus is slightly larger than the scratch copy).
- [ ] Push: commits `ebcf40c` and this one are local only; the user pushes.
- [ ] Carried: SmartRecruiters / Workable JD backfill (5.1 % / 0.8 % coverage); daily schedule; long-tail adapters (iCIMS, Dayforce, Radancy, BrassRing); registry "VERIFY" rows; aggregator keys; cleanup of `db/jobsearch.duckdb.v1-backup-20260915` and the history bundle.

## Run
```bash
.venv/bin/python sweep_ats.py                                   # sweep + JDs + finder stage (now incl. coverage)
.venv/bin/python finder.py setup-check                          # personal files, dependencies, manifest, schema
.venv/bin/python finder.py evidence --check | --rebuild         # evidence manifest -> evidence_units
.venv/bin/python finder.py coverage [--all] [--limit N]         # requirement coverage for survivors
.venv/bin/python finder.py coverage --calibrate                 # thresholds vs hard negatives (§16.1)
.venv/bin/python finder.py mark <id> pass --reason "function: wrong lane"   # a calibration negative
.venv/bin/python finder.py shortlist --days 7 --n 30            # req / role coverage columns
.venv/bin/python -m pytest -q                                   # 78
```
The eyeball and diagnostic scripts used above live in this session's scratchpad; they read `vw_coverage_latest`, `hard_negatives`, `requirement_units.spec` and the stored `matches` / `notes` JSON, all of which are in the DB.
