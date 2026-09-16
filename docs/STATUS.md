# Session Status — Jobsearch

_Last updated: 2026-09-15 night (Claude Code / Opus on Vostro; the fit model retrained on the graded labels). Overwrite at the end of each session; git history is the changelog._

## DONE THIS SESSION: the fit model is retrained on the 3,009 graded labels (§17.5 item 1)
**It worked.** The graded `wrong` / `stretch` rows are now the model's negatives, and the failure the whole
labeling run was built to fix — a vocabulary model that could not tell a bullseye from a senior generalist
sharing its words — is gone. Model **`330a4e0ce441`** replaces `ec851b252dc3`.

### The number that was never measurable before
**AUC of positives vs the graded `wrong` rows: 0.946** (vs `stretch` 0.776; using only graded positives, so both
sides come from the same corpus and the same judge: 0.941 / 0.739). Before this session the only negatives were
1,500 random postings, so no such AUC existed.

**Held-out (out-of-fold) fit by grade — the honest separation:** bullseye **0.75** · adjacent **0.62** ·
stretch **0.46** · wrong **0.19**. The old model's *final scores* by grade were 82.0 / 80.0 / 79.8 / 72.8 — it
told `wrong` from the rest by ~8 points and told the other three apart not at all. That is now a clean gradient.

5-fold AUC **0.947** (was 0.983) and precision@20 **0.990** (was 1.000). **Both falling is the expected and
correct result**: the old figures were measured against random postings, which any vocabulary model wins. The
task is now genuinely hard, and 0.947 is against real near misses.

### Acceptance checks from the handoff
| Check | Before | After | |
|---|---|---|---|
| **Amentum "Business Process Specialist (Mid-Level)"** (graded bullseye, killed by the content gate) | fit **0.12**, rejected | fit **0.744**, score 74, `review`/strong | ✅ **the stated pass/fail test** |
| Henry Schein R134977 (the bullseye) | 96 | **97**, fit 0.992, very_strong | ✅ |
| Capital One "AI Foundations" misfires | ~95, top 15 | **0.026 / 0.044 fit, rejected** | ✅ |
| Centene "Senior Director, Medical Economics" (graded stretch) | 93, within 4 pts of the bullseye | 90, **7 points below** | ⚠️ closer than wanted but ordered correctly |
| Humana "Creative Operations Director" (graded stretch) | in the top 15 | 86, 11 points below | ⚠️ same |
| Booz Allen "Digital Transformation Specialist" (content-gate false negative) | 0.34, rejected | fit 0.669, score 67, `review` | ✅ |
| Included Health "Director, Staffing Transformation & Ops" (bullseye) | — | 94, fit 0.901, candidate | ✅ |

**Band × grade crosstab, good-fit rate** (good = bullseye + adjacent): very_strong **53% → 92%** · strong
**38% → 78%** · partial **20% → 33%** · weak **14% → 0%**. Still monotonic, and far steeper.

**Level 1 miss rate:** of every graded posting now rejected, 35 bullseye + 53 adjacent out of 2,252 = **3.9%**,
down from the ~13% measured on the 599-row reject sample. Different denominator, so treat it as directional
until a fresh reject sample is graded.

> **Read the crosstab and the miss rate as in-sample.** The model was trained on these labels, so those two
> tables flatter it. The out-of-fold figures above (AUC 0.946, fit-by-grade 0.75/0.62/0.46/0.19) are the honest
> ones, and they are what the verdict rests on.

**Rescreen `330a4e0ce441`:** 80,272 rows in 452 s under rules `a844b0d2d80d` — candidate **130** (was 276),
review **819** (was 1,708), reject 79,323. Bands very_strong 123 · strong 358 · partial 403 · weak 65. The
screen got much tighter because the model finally disagrees with senior-generalist vocabulary. Report written:
vault `Search_Results/Jobs_Found_20260915_2139.md`.

**Signal AUCs over labeled rows with a screen:** rule_score 0.669 · **fit_prob 0.941** · blend **0.814**. The
blend now scores *worse than fit alone* — `pipeline.combine`'s weights were set when fit was the weak signal.
Re-tuning that split is the obvious next lever and was not touched here.

### How it was wired (one training path, as specified)
- `vw_label_set` gained a third branch reading `vw_llm_labels_latest`: **bullseye → label 1 weight 1.0 ·
  adjacent → 1 / 0.6 · stretch → 0 / 0.5 · wrong → 0 / 1.0**, plus a `grade` column (NULL for other sources).
- `vw_llm_labels_latest` now puts **`scorer = 'user-adjudicated'` first explicitly** (it previously won only by
  accident of being newest, so any re-grade would have silently overwritten the user's call).
- `SOURCE_PRIORITY` = `user_adjudicated` → `application` → `decision` → `jobs_found_escalated` → `llm_judge` →
  `pseudo_neg`: the user's adjudication outranks everything, the vault outranks the judge.
- `features.training_set` **drops every posting in `training_exclusions`** (35 rows) from *all* sources — that
  removed 3 application and 2 escalated positives, which is the point of the table.
- Graded rows are fuzzy-deduped against higher-priority vault rows but **never against each other** (§17.2: an
  employer's boilerplate makes unrelated roles look alike, so collapsing them would throw labels away).
- `labels.collect` keeps judged postings out of the pseudo-negative sample — a graded posting carries a real
  label and must not be re-sampled as "unlabeled" at weight 0.5.

**Training set: 4,787 rows — 876 positive / 3,911 negative.** application 288 · llm_judge 2,927 ·
pseudo_neg 1,500 · jobs_found_escalated 66 · decision 3 · user_adjudicated 3.

### One contested row left for the user
**Capital One "Senior Manager Data Analytics - People Strategy & Analytics"** — a vault application (positive),
graded `stretch` ("validating analytical tool methodologies and coaching junior data staff is a
data-governance/analytics discipline"). Per handoff decision 4 the vault positive wins and it trains as a
positive. If you would rather it were contested-and-excluded, that is
`finder.py judge exclude --posting <id> --reason ...`. Angi and Zillow needed no action — their
user-adjudicated `wrong` rows correctly beat their vault positives.

## Also done: the blend re-tuned to content 0.90, and the rubric's analytics cap removed

### Level 1 was audited first, because the weight decision depends on it
The gates hold. Recomputed over all 949 survivors: **zero location leaks** — remote 453 · nationwide/remote-
unverified 372 · commutable hybrid 51 · commutable on-site 73, and nothing with 0 location points survives. Pay
works (719 of 949 post a band; the $150K floor rejects correctly). Of the 88 bullseye/adjacent postings Level 1
rejects, the causes are location 68 · outside the US 43 · junior level 16 — the gate doing its job. **Two soft
spots:** 372 survivors (39%) are "nationwide, remote unverified" and survive on an assumption; 3 non-US rows
(2 CA, 1 GB) plus 102 with no country code slipped the country rule.

### The sweep (720 graded survivors, OUT-OF-FOLD fit)
| content weight | AUC | P@20 | P@50 |
|---|---|---|---|
| 0.50 (was) | 0.537 | 0.85 | 0.84 |
| 0.75 | 0.577 | 0.90 | 0.84 |
| **0.90 (set)** | **0.589** | **0.90** | **0.90** |
| 1.00 | 0.592 | 0.90 | 0.88 |

Monotonic. Held at 0.90: 1.00 buys 0.003 AUC and 10% keeps a level/title tiebreaker among postings the gates
let through. `rule_score` is unaffected — `profile_score` renormalizes over the non-content weights.
`rules_version` **`a844b0d2d80d` → `2f74427157f8`**.

**Rescreen: verdicts identical** (candidate 130 · review 819 · reject 79,323) — verdict comes from rule
reasons, not the score. **Bands moved a lot**, which is the point: very_strong 123 → **189**, strong 358 → 241,
partial 403 → 244, weak 65 → **269**. The distribution spread out instead of being dragged to the middle.

| band | good-fit rate at w=0.50 | at w=0.90 |
|---|---|---|
| very_strong | 92% | **95%** (104 bullseye, 75 adjacent, 10 stretch, **0 wrong**) |
| strong | 78% | **85%** |
| partial | 33% | **43%** |
| weak | 0% | **2%** (83 wrong, 43 stretch) |

Named rows: Henry Schein R134977 **99** · Included Health Staffing Transformation **91** · Included Health
Workforce Analytics Model Standardization **86** · Amentum Business Process Specialist **70** (strong) · Centene
Medical Economics 88 (stretch, still high) · Humana Creative Ops 81. Report: `Jobs_Found_20260915_2235.md`.

### The finding that matters more than the weight
In-sample, fit AUC among survivors is 0.925. **Out-of-fold it is 0.592.** Mean OOF fit by grade, survivors only:
bullseye **0.77** · adjacent **0.64** · stretch **0.65** · wrong **0.63**. The model separates bullseyes cleanly
and **cannot tell stretch or wrong from adjacent** among postings that cleared Level 1. The retrain's real win is
on the rejected population (OOF AUC 0.927) — it is excellent at discarding the obviously wrong. The confusable
band is still confusable, and no weight change fixes that; Phase 3 coverage or Phase 4 LLM review has to.
**Caveat that cuts the other way:** many of those unseparated `stretch` rows are analytics roles mislabelled by
the rubric bug below, so part of this flatness may be label error, not model error.

### The rubric bug: 0 of 3,009 postings could ever be a bullseye in the analytics lane
`RUBRIC_PERSONAL` said *"SECONDARY lane (cap at `adjacent`): senior, strategic, leadership-facing data /
analytics / BI work"* and gave the analytics record one clause: *"automating reporting pipelines in SQL and
Python; Grafana, Plotly and Streamlit dashboards."* Consequence, measured: **bullseye by lane = primary 208,
secondary 0.** The cap was structurally binding on 247 secondary-lane rows.

It also cost real grades. Capital One "Principal Associate, Financial Planning & Analysis" → `stretch`:
*"the core work is corporate FP&A, **a distinct finance discipline**"* — the judge called FP&A unfamiliar work
because the record it was shown does not contain FP&A.

**Rewritten from the §5 evidence sources** (`Resume_Bullets.csv`, `Resume_Blocks.csv`, `Bio_Jeff_Professional.md`),
adding what was verifiably missing: the Force-to-Load capacity model (1,000-person field force, demand by day /
hour / shift, $18-22M capacity variance, work priced in minutes with a modified PERT distribution, four versions
in three years); the five-year FWA truck-roll forecast model (**FWA = Fixed Wireless Access, not fraud/waste/
abuse**); FP&A forecasting and budget management ($3B demand vs $2.2B budget, Commitment View and Best View,
DMAIC cycle-time cut of 70%); production data pipelines (Python/SQL over Oracle milestone tables with automated
SPC charts replacing Minitab, the data architecture a data science team trained a prediction model on, a
self-healing 12-source pipeline into PostgreSQL). The blanket cap is replaced by a rule that judges **the object
of the analysis**: operations decisions (capacity, workforce, demand, throughput, forecasting, cost-to-serve) can
be `bullseye`; other objects (marketing, product, risk) are `adjacent`; hands-on engineering IC seats (data
engineer, analytics engineer, data scientist building ML/NLP/RAG) stay `wrong`. `rubric_version`
**`645584b0771e` → `5f0f1755634b`**. Old file backed up outside the repo.

**On the coding-assessment constraint — corrected mid-session.** The first argument for dropping it from the
rubric was that Level 1 owns it. That over-claimed: `ASSESSMENT_GATE_TERMS` and `CODING_TEST_TERMS` only catch
JDs that *say so* (and the coding rule only on tier 3), and `BLOCKED_POSTERS` is a short named list (Crossover).
Most postings that will have an assessment do not mention one. **It still does not belong in the rubric**, for a
better reason: the judge reading the JD has exactly the same information as the regex and cannot predict it
either. The cap was not detecting assessment risk — it was using "is this an analytics role" as a proxy for it,
and that proxy is what killed the workforce-analytics roles the user wants. Assessment risk is discovered, not
predicted; it belongs in `BLOCKED_POSTERS` as it is learned, and in the user's judgement at application time.

### NOT DONE — needs the user's go-ahead
**The re-grade.** The labels in the DB still carry the cap. Scope: the 247 secondary-lane rows plus the ~368
analytics-flavoured `wrong` rows ≈ **600 postings, ~24 batches, ~1.7M tokens**. Every crosstab above is measured
against the OLD labels, so the true picture may be better than reported. `judge export` renumbers batches, so
re-export against `5f0f1755634b` before grading.

## NEXT SESSION: START HERE
1. **Re-tune `pipeline.combine`.** blend AUC 0.814 < fit AUC 0.941 means the blend is now *destroying* signal.
   The weights assume a weak fit model that no longer exists. Highest value, smallest change — same shape as
   this session's win.
2. **Re-calibrate coverage** (`coverage --calibrate`): the 7-negative problem is gone, `vw_hard_negatives` can
   now draw on 2,107 graded `wrong` rows. Then re-run the §15.7 eyeball and only then decide 3b.
3. **The user still wants to eyeball ~100 labels** (`judge report --csv db/snapshots/llm_labels.csv`). The
   rubric line about capacity/workforce-planning frameworks was fixed *after* the run, so `rubric_version` has
   changed and any re-grade will differ from that night's.
4. Grade a fresh reject sample under the new screen to measure the miss rate out-of-sample.

## Active Sprint
@/docs/SPRINT_PLAN.md — §17.5 item 1 (retrain) is **DONE**; §17.7 acceptance boxes 4 and 6 are met. **Phase 3a
is BUILT and its §15.7 eyeball FAILED; 3b and Phase 4 are still not started.** Coverage stays at weight 0. The
3b decision is unchanged and still belongs to the user with Fable — the Phase 3a diagnosis below stands, except
that its worst input (7 hard negatives) is now fixed and a re-calibration is worth running before deciding.

## Known broken (pre-existing, not from this session)
`tests/test_finder.py::test_rescreen_predicate_selects_only_new_changed_or_version_changed` fails on `main` at
`3de36b4` as well — it expects one candidate and gets two. Almost certainly stale since the ingest-audit change
that stamps `description_fetched_at` when text actually changes. **82 of 83 tests pass.**

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

## Ingest audit, prompted by a JD the user pasted (2026-09-15 late)
The user pasted the AHEAD JD he had applied to and asked whether we held that detail. **We did not.** That one
question found a platform-wide ingest bug and cleared a second platform.

- **Lever was storing the wrapper, not the job.** `lever_jobs` read `description` (opening blurb) and `additional`
  (EEO, benefits) and never `lists`, where Lever keeps every duty, requirement and skill section. 506 postings at
  6 employers — AHEAD, Included Health, Aledade, Aprio, FiscalNote, Life.Church — were scored on boilerplate.
  AHEAD's posting went **2,756 → 5,826 chars**; the platform median went **3,297 → 5,808**. Fixed, tested,
  re-swept (no delete needed: the upsert refreshed text in place and kept `first_seen_at` and lifecycle).
- **Re-screening the 502 corrected rows: 4 very_strong · 38 strong · 19 candidate · 66 review** — ~85 postings
  that were invisible an hour earlier. Re-graded by Sonnet (21 batches): **9 bullseye, 15 adjacent**, including
  **Included Health "Director, Staffing Transformation & Operations" (bullseye, score 93)** and Included Health
  "Workforce Analytics Model Standardization Consultant" (bullseye, 79) — the user's own GNO capacity work.
- **A second, quieter bug on the way:** the upsert refreshed `description_text` without touching
  `description_fetched_at`, so the finder never re-screened text an ingest fix had rewritten. Now stamped when the
  text actually changes — **in UTC**, because the finder writes `screened_at` in UTC while DuckDB's `now()` is
  local, and a local stamp read as hours in the past would have silently disabled every future re-screen.
- **Oracle ORC audited and cleared.** Its lower median (3,304 vs Workday's 6,197) is employer mix, not a dropped
  field: the adapter already reads `ExternalDescriptionStr` + `ExternalResponsibilitiesStr` +
  `ExternalQualificationsStr`. Verified against the live API on the user's NFCU "Principal Business Analyst":
  Qualifications 3,302 and Responsibilities 2,019 chars are both present in our 5,056 stored characters. The
  fields we skip are correctly skipped (`CorporateDescriptionStr` is the company blurb, `ShortDescriptionStr` a
  teaser, `Internal*` byte-identical duplicates). **One refinement made:** Oracle returns those sections
  unlabelled, so the splitter could not tell the role section from the person section — the detail fetch now
  writes `Responsibilities` / `Qualifications` headings as it joins them (applies to newly fetched rows).
- **Near-miss worth remembering:** `db/batches_rejects/` was not gitignored and 25 JD batch files were briefly
  tracked; the pre-commit personal-pattern scan caught it and they were dropped from the tip commit before any
  push. `.gitignore` now covers `db/batches*/`.

## The labeling run (sprint plan §17) — 2,573 graded labels, 2026-09-15 night
**Done:** every screen survivor (1,940 postings in 78 batches) plus a deliberate 599-posting reject sample, graded
by Claude Sonnet subagents against `rubric.RUBRIC_PUBLIC` + `RUBRIC_PERSONAL`. **0 rows rejected on import.**
Distribution: **bullseye 205 · adjacent 332 · stretch 319 · wrong 1,717**.

### What it proves about Levels 1 and 1.5 (the question worth the tokens)
| band | bullseye | adjacent | stretch | wrong | n | good |
|---|---|---|---|---|---|---|
| very_strong | 24 | 17 | 17 | 20 | 78 | **53%** |
| strong | 33 | 50 | 43 | 92 | 218 | **38%** |
| partial | 6 | 9 | 6 | 55 | 76 | **20%** |
| weak | 0 | 1 | 1 | 5 | 7 | **14%** |

The rules + fit model order the corpus correctly at the band level — a clean monotonic gradient. **But the score
cannot separate degrees of fit:** mean final score by grade is bullseye 82.0 · adjacent 80.0 · stretch 79.8 ·
wrong 72.8. It tells `wrong` from the rest by ~8 points and tells the other three apart not at all. That is the
precision problem, quantified.

### Level 1's miss rate, measured for the first time (599 graded rejects)
wrong 472 (79%) · stretch 50 · **adjacent 44 · bullseye 33 — about 13% of rejects are work the user should see.**
Cause of each good rejection: not remote / outside commute 57 · outside the US 34 · **content does not fit 24** ·
comp below floor 13 · junior level 9. Location, country and comp rejections are correct. **The content gate is the
defect:** it killed Amentum "Business Process Specialist" at fit **0.12** and Booz Allen "Digital Transformation
Specialist" at 0.34 — literal primary-lane work discarded as noise by the vocabulary model. Retraining with the new
negatives is aimed straight at this.

### Agreement with the user's own behaviour
Of 36 postings the user pursued: **27 agree** (18 bullseye, 9 adjacent), 9 contested (5 stretch, 4 wrong) — 75%.
Reviewed row by row with the user 2026-09-15:
- **Judge right (4):** Angi Principal Analytics Engineer (dbt/Snowflake IC, assessment-gated), Zillow Senior Talent
  Intelligence Analyst (market research; the overlap was mode, not object), both Capital One data-analytics roles
  (econometrics / model-risk validation).
- **Judge partly right (1):** Airbnb Senior Programs & Business Operations Lead — graded `wrong`, but the posting
  exists because "no one owns the demand-side merchandising strategy", which is the user's own pattern. Stretch.
- **Unjudgeable (2 of the contested, plus 1 more):** Capital One Sr. Business Manager, AHEAD Senior Manager
  Enterprise Transformation, ADF General Application — the stored text is competency boilerplate or marketing copy.
- **Judge WRONG (1), and it is a rubric bug:** Fannie Mae "Strategic Workforce Planning - Principal" asks for
  designing an enterprise workforce-planning **framework**, buy-in without authority, and workforce cost/capacity
  trade-offs in a regulated environment — the GNO capacity model. The judge downgraded it because the work sits in
  HR. `RUBRIC_PERSONAL` already says capacity-planning **models** are primary lane and only the staffing cycle is
  not; the judge applied "domain-gated" to a department instead of to the object of the work. **Fix the rubric line
  before the next run.**

### Contested labels are excluded, not overruled (user decision)
The user pushed back on "your decisions outrank the judge", correctly: pursuit decisions were made under pressure
and are noisy positives. A conflict now means the row is **contested and trained on by neither side**. New table
`training_exclusions` (schema v6) plus `finder.py judge exclude --posting <id> --reason ...`, and an auto-rule that
retires any posting the judge called too thin to read (**34 caught**, plus ADF and AHEAD by hand).

## Live run 2026-09-15 20:11 — coverage on the live DB, second report written
- **A WSL crash at 19:42 killed the first attempt** mid-coverage (evidence stage had finished at 19:39:59). Nothing
  was lost or corrupted: `requirement_units` commits per 200-posting batch, so 17,038 units survived and the plain
  rerun resumed. **Coverage is crash-resumable; just rerun `finder.py coverage && finder.py report`.**
- Live totals: evidence 2,888 units (version `74156dda6991`, 4 min) · coverage **1,983 postings in 870 s** (partly
  warm) · report written at 20:11:47 → vault `Search_Results/Jobs_Found_20260915_2011.md`.
- **Comparison with the 18:21 report** (both pipeline files, 150 summary rows each): the summary tables are
  **identical — 150 rows in both, none added, none dropped**, confirming §16.6 held (coverage at weight 0 changed no
  score). **Zero block overlap**: the 14-day `surfaced` rule pushed the blocks to ranks 16–30, so the two files
  together give 30 escalated JDs rather than the same 15 twice. The new file's Fit stanzas carry the coverage fields.
- **New finding from reading those stanzas — company boilerplate is being scored as requirements.** Reported gaps
  include "Strong interest in Angi, home services, marketplaces…", "To learn more about the culture, rewards and
  benefits…", "San Antonio, TX, Charlotte, NC, Tampa, FL or Phoenix, AZ.", "At Caylent, our people always come
  first.", "Disability and life insurance". These are intro / benefits / location text that `split_requirements`
  admitted into the required and role groups, where they can never match evidence and drag every JD toward the same
  middling score. That is a second, independent cause of the flat ~50 distribution, and it is fixable without
  touching the encoder: tighten `DROP_HEADINGS` / intro handling and drop units that are marketing or benefits text.
  The `not_in_record` tagging works correctly in the same stanzas ("… (e.g., PMP, CIPS) is a plus. [not_in_record: pmp]").
- **Logging note:** Python block-buffers stdout through a pipe, so these run chains look silent until they finish.
  Use `python -u` in future background chains.

## Option A was prototyped and also fails (2026-09-15, scratch DB, read-only)
Contrast scoring — score each requirement by how far its best evidence cosine stands above that requirement's own
baseline against the whole evidence store — was measured on the stored vectors (no re-embedding). Variants: `gap`
(best − mean), `z` ((best − mean)/std), `top5` (mean of the 5 best − mean), `abs_best` (the current absolute cosine)
and `gap_kw` (kind weight applied before the max). Over 1,772 postings with ≥ 3 required work units:

| variant | AUC pos vs audit | vs fit_top | vs pseudo | Henry Schein rank | worst misfire rank |
|---|---|---|---|---|---|
| gap | 0.47 | 0.50 | 0.62 | — | Centene VP Medicare **40** / 1,772 |
| top5 | 0.48 | 0.57 | 0.75 | 242 | Novartis AI Foundations **84** |
| abs_best | **0.73** | 0.50 | 0.75 | 360 | Novartis 725 |
| gap_kw | 0.48 | 0.65 | 0.63 | 859 | Humana Creative Ops **152** |

No variant puts the bullseye above the misfires consistently, and every variant's top 8 is dominated by engineering
and consulting roles (GitLab Staff Backend Engineer, Guidehouse Data Platform Lead, Databricks Field Engineering,
Perficient Adobe Commerce). **Caveat:** only 21 labeled positives have coverage rows on this corpus, so the AUCs are
noisy; the named-row ranks are the interpretable signal, and they are bad. Conclusion: the ceiling is the sentence
encoder's discrimination on this text, not the band scheme layered on top of it. Option A is not worth building.

**Analysis caveat for anyone re-running this:** DuckDB's `fetchnumpy()` returns NULL DOUBLEs as `NaN`, not `None`,
and `requirement_units.spec` is written only for the units that survive the 40-unit cap — so a naive
`spec is not None` guard silently poisons every JD with more than 40 work units. The first prototype run was invalid
for that reason (`nan` scores, AUCs of exactly 0.500). Production is unaffected: `score_units` computes specificity
in memory for all work units before capping.

## Options for 3b (not built; the user decides with Fable)
- ~~**A. Contrast instead of absolute bands.**~~ **Prototyped 2026-09-15 and rejected** — see the section above.
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
- [ ] **Bug: the term tiers are not in the coverage cache key.** `evidence_version` hashes unit ids + model only, so
      editing `not_in_record` / `light_in_record` leaves existing `coverage` rows untouched and `coverage` reports
      "0 postings" instead of re-scoring. Fold a hash of both lists into `evidence_version` (re-scores from the unit
      cache, no re-embedding). Tonight's live run is unaffected: the live DB had no coverage rows.
- [x] ~~Confirm the `not_in_record` starter list~~ — confirmed by the user 2026-09-15 and applied before the live run:
      `not_in_record` = Prosci certification / certified, PMP, Azure; `light_in_record` = Power BI, Tableau, Looker,
      Qlik, ThoughtSpot, Prosci (bare), CSM, AWS, GCP. Resume rule unchanged: never claim Power BI or Tableau.
- [ ] Run the live DB through `evidence --rebuild` → `coverage` when 3b lands (cold cost ≈ 25 min; the live corpus is slightly larger than the scratch copy).
- [ ] Push: commits `ebcf40c` and this one are local only; the user pushes.
- [ ] Carried: SmartRecruiters / Workable JD backfill (5.1 % / 0.8 % coverage); daily schedule; long-tail adapters (iCIMS, Dayforce, Radancy, BrassRing); registry "VERIFY" rows; aggregator keys; cleanup of `db/jobsearch.duckdb.v1-backup-20260915` and the history bundle.

## Run
```bash
.venv/bin/python sweep_ats.py                                   # all stages, report written last
# by hand, same order — never stop before the report:
.venv/bin/python finder.py labels --report && .venv/bin/python finder.py train --report \
  && .venv/bin/python finder.py rescreen-all && .venv/bin/python finder.py sync \
  && .venv/bin/python finder.py evidence --rebuild && .venv/bin/python finder.py coverage \
  && .venv/bin/python finder.py report
.venv/bin/python finder.py setup-check                          # personal files, dependencies, manifest, schema
.venv/bin/python finder.py evidence --check | --rebuild         # evidence manifest -> evidence_units
.venv/bin/python finder.py coverage [--all] [--limit N]         # requirement coverage for survivors
.venv/bin/python finder.py coverage --calibrate                 # thresholds vs hard negatives (§16.1)
.venv/bin/python finder.py mark <id> pass --reason "function: wrong lane"   # a calibration negative
.venv/bin/python finder.py shortlist --days 7 --n 30            # req / role coverage columns
.venv/bin/python -m pytest -q                                   # 78
```
The eyeball and diagnostic scripts used above live in this session's scratchpad; they read `vw_coverage_latest`, `hard_negatives`, `requirement_units.spec` and the stored `matches` / `notes` JSON, all of which are in the DB.
