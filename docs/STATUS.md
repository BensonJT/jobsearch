# Session Status — Jobsearch

_Last updated: 2026-09-17 (Claude Code / Opus), after two days of work: the ext4 move, Postgres evidence, and seven coverage experiments. Overwrite at the end of each session; git history is the changelog._

**Catch-up order for a fresh session (e.g. Fable):** this "NOW" section → `docs/SPRINT_PLAN.md` §19 (what was built, results, proposals) → `docs/COVERAGE_EXPERIMENTS.md` (per-run detail and Conclusions). Tests: **131** passing.

## NOW — the repo moved, coverage recalibration ran, experiments in flight (2026-09-16)
**Location.** The repo lives at **`~/jobsearch` on the WSL ext4 disk**. The E: copy (`/mnt/e/code/jobsearch`) was deleted at
the user's request after a byte-level check. Why: `/mnt/e` is a 9p mount served by Windows, and torch/transformers
imports over it failed under Windows memory pressure (bus error, ENOMEM on `open()`, one WSL crash). The one file
kept on E: is the pre-compaction backup, `E:\backups\jobsearch\jobsearch.duckdb.precompact-20260916` — delete once a
sweep has run clean. `.env`, `evidence.local.toml`, `*_local.py`, `.personal_patterns` and `db/` were copied by hand
(a clone does not bring them). The Linux disk is a VHDX on C:, which is nearly full — see "Storage" below.

**Evidence now reads PostgreSQL** (`b1c9d3d`). Bullets, duty statements and claim guards come from
`resume.vw_resume_bullets` / `vw_resume_blocks` / `vw_resume_guards` via a new `postgres` source type
(`path = "$RESUME_DB_URL"`, set in `.env`). `evidence_units` is a cache: `ensure_current` re-embeds only changed units
before coverage/calibration, and a rebuild refuses to empty a source that is unreachable.

**The recalibration finished — coverage does not rank.** Full record, one section per run:
**`docs/COVERAGE_EXPERIMENTS.md`**. Short version (AUC):

| Run | coverage vs hard neg | coverage vs stretch | fit_heldout vs stretch |
|---|---|---|---|
| R2 baseline | 0.559 | 0.575 | 0.955 |
| S1 core evidence only | 0.543 | — | — |
| S2 "<title>: <requirement>" | 0.607 | 0.610 | 0.955 |
| S3 bge-base encoder | 0.566 | 0.628 | 0.955 |
| S4a MiniLM cross-encoder rerank | 0.604 | **0.669** | 0.955 |
| S4b rerank + title context | 0.617 | 0.664 | 0.955 |

Findings: (1) the fit model already separates positives from `stretch` at 0.955 held-out; (2) the `fit_top` hard
negatives are chosen FOR high fit and, after reranking, look like real fits (McKesson Lead Workforce Intelligence
Consultant, Capital One Product Operations PM) — a biased calibration target; (3) the reranker removes the
engineering-role false positives, so coverage's value is as a trustworthy **explainer**, not a ranker; (4) S4a's
thresholds hit the grid edge (0.95 / 0.05), so continuous credit is the next candidate.

**Experiments finished 2026-09-17 01:52** — S4b, S3 and S2c are recorded, with a Conclusions section at the end of
`docs/COVERAGE_EXPERIMENTS.md`. Short version: coverage never ranks (best 0.669 vs the fit model's 0.955 on stretch);
the MiniLM reranker without title context (S4a) is the configuration to keep if coverage becomes an explainer; title
context and bge-base add little. All scratch DBs deleted; the live DB was never touched.

**Experiment switches** (env, unset = production): `JOBSEARCH_REQ_CONTEXT=title`, `JOBSEARCH_RERANKER=<model>`,
`JOBSEARCH_RERANK_TOP=<n>`. `requirement_units` has no model column in its primary key, so switching modes or models
replaces cached rows — run each variant on its own DB copy. Calibration now also reports AUC vs `stretch` and vs
judge-confirmed `wrong` only.

**Decisions waiting on the user.** (a) Whether coverage becomes an explainer only (weight 0 in ranking, matches shown
in the report) — the evidence points that way. (b) Replace `fit_top` as a calibration target with judged rows.
(c) Storage: the Linux VHDX on C: is 122 GB (85 GB used; Meridian's Postgres is 35 GB) with 30 GB free on C:.
Options: compact the VHDX (~37 GB back), and/or a second VHDX on E: mounted into WSL for Meridian's data and `db/`
(native speed, off C:, WSL still boots without the drive). Needs admin PowerShell + `wsl --shutdown`.
(d) **Parked idea from the user — do not lose it:** if coverage becomes a stored dimension, use its per-requirement
matches to shortlist resume bullets for the job application skill (Keystone vault
`Professional/Areas/Job_Search/Tools/IDEA_Coverage_Bullet_Selection.md`). Prerequisites: matches must carry `bullet_id`
(bullet source `ref_columns` is position + project today), keep every requirement's top evidence rather than the top 5
per posting, and a `--jd-file` entry point for JDs that are not swept postings.
(e) **A third grading lens for AI work (raised by the user 2026-09-17).** The judge grades two lenses today
(`grade_process`, `grade_technical`; `LENS_VIEWS` in `features.py`, prompt in `rubric.py` + `rubric_local.py`). Roles
built on applied AI — enablement, adoption, governance, agentic workflow delivery — have no lens of their own, so they
land as `wrong` on both. Worked example: Navy Federal *Principal AI Engineer (Agentic AI)*, req 31189 (posting
`101023530e516abcfd93`) — judged `wrong`/`wrong`; the user's read is a PARTIAL fit on AI skills, not strong enough to
apply (hands-on Azure AI Foundry, distributed Python services, AI security threat modeling, 7–10 yrs in AI). The lens
must separate AI-enablement/delivery roles (a real fit) from hands-on AI platform engineering seats (still out of
lane), and respect the coding-assessment constraint. Needs: an `ai` lens block in the rubric, `grade_ai` in the label
schema + a `vw_label_set_ai` view, a regrade of the labeled corpus (~3,000 postings through the Sonnet batch judge), and
a third lens model. Design with the user before building.
Then: the report-feedback review (`level_fit` column) and the QUEUED level ceiling below.

**Commits since the last push (19 incl. this handoff, all local, `72167e5` onward):** lens calibration OOF fix · judged-wrong hard
negatives · three STATUS handoffs through the crashes · Postgres evidence source (`b1c9d3d`) · ext4 move in CLAUDE.md
(`621fec4`) · experiment switches + stretch AUC (`e5cbc39`) · judged-wrong AUC (`d8fe17a`) · OOF fit for hard
negatives (`1566e32`) · the S2a–S2c / S3 / S4a / S4b records and Conclusions · the bullet-selection idea and the AI
lens (STATUS). Ask before pushing; run the `.personal_patterns` scan first (known 3-line baseline:
`backend/profile.py:111`, two lines in `tests/test_finder.py`).


## QUEUED — a level ceiling in the rule engine (raised 2026-09-16 during the user's report review)
**Why.** Reviewing `Report_Feedback_20260916.csv`, the user found most of his `wrong` calls were about **level and
scope**, not function: AVP / Senior Director postings well above any role he has held, usually bundled with deep
industry tenure. Of the ten rows he had marked `wrong`, only three were about the work. The screen has the
defect in the opposite direction: senior signals **award** level points with no ceiling (§14: senior = 100),
which is a large part of why 170 of the 232 surfaced rows landed `very_strong`.

**Decision (with the user).** Level is written plainly in the JD, so it gets a **deterministic rule, not a trained
model** — the fit model is deliberately blind to level words (§13 `MODEL_STOP_WORDS`) and cannot learn it anyway.
Human labels are the rule's **test set**, not training data.

**Signals for the rule** (Required block and title): title tier AVP / VP / SVP / Head of / Chief / Senior Director;
"N years managerial / people leadership" requirements; org-building language ("build and lead a … organization",
"global teams", "spans of control", "executive candidate"); team size above `MAX_DIRECT_REPORTS`; P&L ownership.
Several hits → `out_of_reach`, one → `stretch_up`, none → `in_range`. Worked example: Amgen "Associate Vice
President, AI&D Scaled Operations and Transformation" hits title, 7 yrs managerial, org-building and spans of control.
Note the nuance there: the written minimums ("Master's + 10 yrs", "7 yrs managerial **or** leading programs /
directing resources") are nearly met — the reach problem is the org-building scope, not the stated minimums.

**Schema.** `report_feedback` gains `level_fit` (the human label; already added to the vault CSV as column L, along
with `grade_before_split`, `needs_confirm`, `split_reason`). `screens` gains a computed `level_fit` from the rule.
Then measure rule-vs-human agreement, and only after that change how level feeds the score.

**Grading convention the user adopted with it.** `human_grade` = is this my kind of work, ignoring level and
industry; count the distinct kinds of work never owned: none = bullseye, one = adjacent, two or more with real
overlap = stretch, almost none = wrong. Scale goes in `level_fit`, gates and logistics in `verdict`.
Content not read or posting dead → grade blank.

## Earlier on 2026-09-16 (before the recalibration) — kept for the open items at the end

Nine commits from that session were pushed; the history rewrite of `9ab7755` is on the remote (verified).

The four queued items are done: the corpus is rescreened under current rules, the three clamped boards
enumerate fully, every row carries a per-lens fit, and the three lens lists are written and waiting for
review.

| commit | what |
|---|---|
| `ba6a327` | **Rewrite of `9ab7755`** with the compensation figures removed from this file |
| `ce151f1` | A flag that says "this is reachable" must not cost points |
| `461d4b7` | Partition plan builder: enumerate a clamped board one facet value at a time |
| `a10896a` | Per-lens fit on every row: `screens.fit_process` / `fit_technical`, `vw_lens_fit` |
| `22f0ac1` | The three lens lists, and two CLI commands that were documented but never built |

Test count then was 128 (`a10896a`'s message says 134, which was wrong); it is **131** after 2026-09-17.

## Still-open items from that session (the "NOW" section above takes priority)
1. ~~**Force-push.**~~ **DONE** — `9ab7755` confirmed off the remote 2026-09-16 after the crash. ~~`ba6a327` replaces `9ab7755`; until it lands, the comp anchor is still on the public
   remote. `git push --force-with-lease origin main`. Then reset the OptiPlex mirror rather than merging
   into it — its history diverged.
2. **Review `Lens_Lists_20260916_1343.md`** in the vault's `Search_Results`. 200 `both`, 540 `process`,
   222 `technical` actionable. The top of the `both` list is the point of the whole two-lens exercise.
3. **A sweep has not run since the partition landed.** The three boards were pulled live as an acceptance
   test but nothing was ingested, so roughly 760 previously-unreachable reqs are still outside the corpus.
   The next `sweep_ats.py` picks them up and will need JD budget for them.
4. **Still queued, untouched:** the "rules reject but model confident" review queue; a SuccessFactors
   adapter; near-duplicate req dedupe.
5. **`pipeline.combine` blend weights** (sprint plan 18.9, last open box): content sits at 0.90 from the
   single model; a two-lens content score may want its own blend. The lens scores are deliberately inert
   until that is decided.
6. **Adjudication is still the user's.** He is writing an adjudication file himself. Do not record
   `user-adjudicated` labels ahead of it.

## Personal data was live on the public remote (2026-09-16, resolved pending a push)
`git ls-remote` confirmed `9ab7755` was on `origin/main`, and its `docs/STATUS.md` carried the
compensation anchor and a posted band verbatim, in the Bausch + Lomb comparison table. Both numbers
are in `.personal_patterns`; the repo's own pre-commit scan was never run on that commit. **The
figures are deliberately not repeated here — they live in the vault.**

They appear in **that commit only**, so the fix is one rewrite: `ba6a327` is `9ab7755` with the line
redacted. **User's ruling: scrub the comp figure only.**

**The scan is not expected to come back empty.** Two other patterns — a clearance level and a first
name — still match at `backend/profile.py:111` and `tests/test_finder.py:1261-1262`, and they go back
to `32d38d8`. The user decided they stay: far less sensitive on a repo already under his own name.
**That is the baseline — two files, three lines. Anything else the scan prints is new and must be
dealt with before committing.**

`refs/remotes/origin/main` is now the only ref holding the old commit. The force-push removes it.

**Run the scan before every commit — including on this file.** It is one line, it was skipped on
`9ab7755`, and writing up the incident is itself a way to reintroduce the very strings it is about.
```bash
git grep --untracked -n -i -E -f .personal_patterns -- . ':!.personal_patterns' ':!LICENSE'
```

## 1. The clearance ruling only worked after a SECOND fix
The first `rescreen-all` propagated the clearance and domain-tenure rules to all 63,453 active rows
(456 s) and the verdict diff was **+7 candidate / −7 review / +15 reject**. Nothing like the "batch of
federal-contractor roles surfacing" the last handoff predicted.

Two things were wrong with that prediction, and both are worth keeping:

**Clearance has only ever been a flag, never a rejection.** CACI "Business Process Consultant" (93) and
Guidehouse "Senior Business Process Analyst" (91) were never flagged away — they were already sitting at
`review` with those exact scores. A verdict-count diff is the wrong instrument for a flag change.

**The reclassification worked; the scoring did not.** Measured old-rules vs new over the same 63,438 rows:

| | before | after |
|---|---|---|
| blanket "likely unreachable" flag | 11,351 | — |
| "must already be held -- likely unreachable" | — | 5,340 |
| "is sponsored (ability to obtain) -- reachable" | — | 3,858 |
| no clearance flag at all (boilerplate) | — | 2,153 dropped |
| domain-tenure flag | 1,194 | 1,035 |

So **6,011 postings were correctly reclassified — and only 52 rows moved score**, because the new
"reachable" flag was still penalized 5 points exactly like the flag it replaced. 3,858 postings traded
one penalty for another, and the remaining ~62k are `reject`, which scores 0 regardless.

`^clearance is sponsored` is now in `UNPENALIZED_FLAG_PATTERNS` (`ce151f1`). After the second rescreen
(607 s, rules `16fa57dbeded`) the ruling finally pays: **132 non-rejected postings gained 5 points**,
14 moved `strong` -> `very_strong`, and the federal-contractor roles surfaced as predicted —

| posting | before | after |
|---|---|---|
| CACI "Business Process Consultant" | 93 | **98** |
| Guidehouse "Senior Business Process Analyst" | 91 | **96** |
| Guidehouse "Senior Financial Transformation Consultant" | 89 | **94** |
| CACI "Process Specialist" | 88 | 93 |
| Guidehouse "Change Management / Communication Lead" | 86 | 91 |

**Generalize this.** A flag whose text says the thing is *fine* must be in `UNPENALIZED_FLAG_PATTERNS`,
or splitting a bad flag into a good one and a bad one buys nothing.

## 2. Partition: the three clamped boards now enumerate fully
`facets.resolve_partition` builds the plan; the executor already ran it. A facet qualifies only when it
is **flat** (its parameter is the filter key — a nested location group answers HTTP 400), every value is
under the 2,000 ceiling, and its counts **sum to the board's `timeType` total**. That sum is the only
evidence the facet is single-valued AND covers every posting: a multi-valued facet sums over it, an
incomplete one sums under it.

**It takes the smallest largest-value, not the fewest pulls.** Leidos offers `Is_Evergreen` (2 pulls,
largest 1,863 — 137 reqs from clamping again) and `jobFamilyGroup` (27 pulls, largest 917). Headroom is
worth 25 extra pulls. Sentara has no choice: only `timeType` covers it, largest 1,727.

| board | ceiling said | really has | facet | pulls | largest | result |
|---|---|---|---|---|---|---|
| Booz Allen | 2,000 | 2,396 | `jobFamilyGroup` | 4 | 1,177 | 2,396 pulled, close-pass OK |
| Leidos | 2,000 | 2,210 | `jobFamilyGroup` | 27 | 917 | 2,209 pulled, close-pass OK |
| Sentara | 2,000 | 2,157 | `timeType` | 3 | 1,727 | 2,155 pulled, close-pass OK |

**The build-time sum test is necessary but not sufficient, so the pull re-checks itself.** The first
acceptance run came back 2,392 of 2,394 on Booz Allen and correctly refused the close-pass. That was
not a coverage gap — the board moved to 2,396 during the 100-second pull. So `workday_jobs` now probes
the true total **before and after** and forgives a shortfall only up to the churn it measured. A gap
larger than the churn still marks the pull truncated, because closing reqs a bad facet never looked at
is the 1,380-false-takedown bug again.

`finder.py facets [--discover]` now exists. `store.py` had claimed since the table was added that
discovery is "captured by `finder.py facets --discover`"; it never was — the last session ran it by hand.

## 3. Per-lens fit on the whole corpus (sprint plan 18.8, done)
Schema **v8**, additive: `screens.fit_process` / `fit_technical`. Filled on **60,391** active rows —
every row that has JD text. Stored and reported **only**: `combine` does not read them, so `final_score`
and `model_version` are unchanged.

`lens_scores` computes probabilities with no term attribution. Explaining a score is the main model's
job; per-row attribution for two more models triples the expensive half of the screen for output nobody
reads. The full rescreen with both lens models ran 607 s against 456 s without them.

**Both thresholds are calibrated, as SQL macros so the views and the CLI read one source.**

**Correction, same session.** The first calibration scored the graded rows with a model trained on
them and quoted P 0.97 / R 0.83 at 0.70. That is in-sample and not evidence. Out of fold the same
threshold is **P 0.87 / R 0.61** (process) and **P 0.79 / R 0.55** (technical). The rule: a model's
numbers on its own training set are never quoted — run `cross_validate` or say nothing.

**The overnight per-lens training result stands and reproduces.** OOF mean probability by grade:

| | bullseye | adjacent | stretch | wrong | AUC |
|---|---|---|---|---|---|
| process | 0.797 | 0.678 | 0.509 | 0.217 | 0.951 |
| technical | 0.784 | 0.634 | 0.430 | 0.192 | 0.950 |

Monotonic across all four grades on both lenses — the levels ARE distinguished, which is what the
two-lens retrain was for.

**What the models do and do not do, measured separately:**
- **strong vs not-strong: AUC 0.924 / 0.918.** Strong. This is what the lists rely on.
- **bullseye vs adjacent: AUC 0.676 / 0.696.** Weak but real — better than chance, not usable as a
  grade. The distributions overlap heavily (bullseye 0.797 ± 0.18 against adjacent 0.678 ± 0.21).
  An earlier note in this file called it "a coin flip"; that was wrong, and it came from reading a
  precision figure that is depressed by the class imbalance (358 bullseye against 641 adjacent)
  rather than an AUC.

So an ungraded row is never handed a predicted bullseye. It earns `both` by clearing
`lens_standout_p()` = **0.80**, a probability statement the models can support, and that bar is
understood to be soft. Decision 1 of §18.7 (`both` needs more than adjacent/adjacent) survives.

`lens_strong_p()` stays at **0.70**. The bucket counts barely move between 0.60 and 0.70 (`both`
208 -> 200, `process` 574 -> 540) because almost nothing in the surviving set sits near the
boundary, so the correction changes the confidence attached to a `model` row, not which rows appear.
If the `both` list wants tightening, the lever that actually bites is requiring the standout bar on
**both** lenses rather than either: that takes `both` from 206 to **48**.

## 4. The three lens lists
`finder.py lenses` writes `Lens_Lists_YYYYMMDD_HHMM.md` to the vault's `Search_Results`. Buckets are
disjoint and each is ranked separately (§18.9: do not merge them into one ordering).

| lens_source | both | process | technical | neither | total |
|---|---|---|---|---|---|
| user | 1 | 0 | 1 | 1 | 3 |
| judge | 234 | 749 | 290 | 1,589 | 2,862 |
| model | 366 | 875 | 528 | 58,819 | 60,588 |

Actionable (not `reject`, not decided, not in the tracker): **both 200 · process 540 · technical 222**.
`judge+model` came out empty, which confirms the re-grade covered both lenses on every judged row.

**Lists rank on `final_score`, with `lens_source` only breaking a tie.** Sorting by evidence weight
would bury a model row at 92 under a judged row at 55, and the point of scoring the whole corpus was to
stop the judged 3k being the only thing visible. The lens cells print the judge's word where there is
one and `~0.83` where there is not, so the two are never confused.

Top of the `both` list: Henry Schein "Senior Manager, AI Transformation & Process Excellence" (99,
bullseye/adjacent, $114–178K, remote, 2 days old); Humana "AVP, Corporate Development Integration &
Value Creation" (98); McKesson "Senior Financial Analyst, Transformation and Value Realization" (97,
bullseye/**bullseye**). Best model-only finds, none of which the judge has read: GE Vernova "Services AI
Portfolio and Governance Leader" (94, p0.99/t0.89), Microsoft "Program Manager, Analytics" (91,
p0.92/t0.99), Autodesk "Data Scientist, FP&A Solutions" (93, t0.98).

## The defrag is done — 1,359 MB -> 650 MB
DuckDB has **no in-place `VACUUM`**: deleted pages are reused, never returned to the filesystem. The
reclaim is `ATTACH` a fresh file plus `COPY FROM DATABASE`, which took 27 s and gave back **709 MB**,
far more than the ~100 MB expected from the day's deletes.

Verified before the swap: all 20 tables, 553,057 rows, counts identical on both sides. Then
`store.connect()` on the new file to reassert views and macros — schema v8, 63,453 active postings,
373,163 screen rows, the lens macros and `vw_lens_fit` all intact.

The pre-swap file is kept as **`db/jobsearch.duckdb.precompact-20260916`** (1.36 GB). Delete it once a
sweep has run clean. Two other stale files are still sitting there: `finder_scratch.duckdb` (1.1 GB) and
`jobsearch.duckdb.v1-backup-20260915` (68 MB).

## The rescreen trap (established 2026-09-16, worth not re-learning)
`sweep.run` calls `pipeline.daily(since=stats["started"])`, and `_candidate_sql` ANDs that on top of
the rescreen predicate:

```sql
AND (p.first_seen_at >= ? OR p.description_fetched_at >= ?)
```

So on a routine sweep, `rules_version != ?` / `model_version != ?` are **necessary but not sufficient**
— the row must also have been first seen or re-fetched in that run. **After any rules or model change,
run `rescreen-all` explicitly.** Changed JD text is handled automatically: the upsert bumps
`description_fetched_at` only when the text actually differs, and the screen stage runs after detail.

## The Workday `total` clamp
Accenture reports `total=2000` against a real count of ~44,187. Detection must use a **single-valued**
facet: a posting in three cities counts three times in the location facet and `workerSubType` is
multi-valued too, which called Autodesk and Guidehouse clamped when both are complete. `timeType` is one
value per posting. **Probing past the ceiling is NOT a usable test** — Workday answers any out-of-range
offset with page 1, so even a genuine board looks like it has more.

Accenture stays on `country` (44,216 -> ~731 US). Its US facet is applied and verified; the three boards
above expose no country facet at all, which is why they needed a partition.

## `board_facets` / `board_scope` and the plan executor
Ask each board what it can filter by; never hardcode a facet id. `plain` = one unfiltered pull,
`country` = one filtered pull, `partition` = one pull per facet value unioned on the req key,
`truncate` = pull what we can and block the close-pass.

**Three tenant behaviours, and only a live probe tells them apart:** applied correctly (Accenture);
rejected with HTTP 400 (Booz Allen, Sentara); accepted and silently ignored (GE Vernova returned an
unchanged total and French locations). `discover_and_record` probes every resolved scope for real,
country or partition, and discards what does not actually filter.

**The filter key is not the tree's parameter name.** Workday nests countries under `locationMainGroup`
-> "Country" but you filter on **`locationCountry`**. US matching is by **exact descriptor** — `"United"`
also matches United Kingdom and United Arab Emirates.

## Judge variance is real
Guidehouse posts the same "Senior Business Analyst" as reqs 43463 and 43549, **99.994% identical text**,
graded `stretch`/`adjacent` overall and `adjacent`/`bullseye` on the process lens. The model scored both
identically. So "the same JD and rubric produce the same grade" is **false**, and re-grading is not pure
waste. Across 85 near-duplicate graded groups, 21 (25%) show the judge disagreeing with itself — an
upper bound, since same employer/title/pay does not guarantee identical text.

The user adjudicated that pair himself and sided with the **lower** grade: strong process components, but
the role is heavy on requirements documentation and user stories, which he has not done much of outside
~1 year as a scrum master. Related record gap: he *is* writing product requirements now — Forester,
Meridian, jobsearch — and none of it is in the evidence the judge reads.

## Three rules bugs, all found by the user checking reqs by hand — plus a fourth found by measuring
1. **Clearance** (`740c9a7`) — ~6,000 postings mis-flagged.
2. **Domain tenure** (`a797478`) — a disjunctive list naming a field he has is not a gate.
3. **Not fixed, deliberately:** `off-function title` and `sales/revenue ops scope`. All 5 active
   "excellence"-titled postings hitting the first are genuinely off-lane, and 7 of 8 hitting the second
   are genuinely sales/BD. The review queue is the fix, not loosening rules that are right 7 times in 8.
4. **The penalty on the new "reachable" flag** (`ce151f1`) — found only by diffing the rescreen instead
   of trusting the verdict counts. See §1.

**The pattern: three of four were invisible until someone checked the output against the world.** The
"rules reject but model confident" review queue is still the right next build — the Bausch + Lomb
Director is `reject` by rules and 0.99+ on both lens models, and that contradiction is discarded
silently.

## SuccessFactors IS ingestible (adapter not built)
The generic host `career2.successfactors.eu` does not paginate. The **branded** host does:
`https://careers.bauschlomb.com/search/?q=&sortColumn=referencedate&sortDirection=desc&startrow=N`
pulled 172 of 173 reqs. Detail pages work via `/job/<slug>/<id>/` on the branded host. **The rule is:
find the employer's branded career host, not the generic one.** Common in pharma and medical device —
worth counting target employers on it before building.

## Carried over
- SmartRecruiters / Workable JD backfill; daily schedule; long-tail adapters (iCIMS, Dayforce, Radancy,
  BrassRing); registry "VERIFY" rows; aggregator keys.
- Cleanup of `db/jobsearch.duckdb.v1-backup-20260915` and the history bundle.
- Coverage/Phase 3b still blocked; `vw_hard_negatives` can now draw on 1,361 graded `wrong` rows instead
  of 7 audited ones, so re-calibrate before deciding.
- `rubric_local.py` is gitignored; its backup is vault `Tools/Finder_Build_Personal_Appendix.md` §2,
  synced at `897123f3fc93`. Re-sync whenever the rubric changes.

## Run
```bash
.venv/bin/python -u sweep_ats.py                 # all stages; --no-report to skip the vault file
.venv/bin/python finder.py rescreen-all          # REQUIRED after any rules/model change
.venv/bin/python finder.py facets --discover     # re-resolve every board's filter scope
.venv/bin/python finder.py lenses                # the three lens lists
.venv/bin/python -m pytest -q                    # 128
```
