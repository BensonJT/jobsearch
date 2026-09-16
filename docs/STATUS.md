# Session Status — Jobsearch

_Last updated: 2026-09-16 (Claude Code / Opus, day session). Overwrite at the end of each session; git history is the changelog._

## Where this left off

Five commits, **local and unpushed**. The corpus is US-only, the ingestion bug that was silently
throwing away most of four boards is fixed, both per-lens models are trained, and a user ruling
unblocked ~6,000 postings that a bad clearance rule had flagged away.

**Nothing has been rescreened yet.** `rules_version` moved `2f74427157f8` -> `287640fe1817` (the
clearance fix), so every score in `screens` is stale with respect to the current rules. A normal
sweep will NOT propagate that -- see "the rescreen trap" below.

| commit | what |
|---|---|
| `8ea32db` | Workday CXS clamps `total` at 2000: detect, scope to US, never close-pass |
| `ff691c7` | A fit model per lens (18.8) |
| `3ac4b51` | `board_facets` discovery; clamp detector corrected to a single-valued facet |
| `740c9a7` | Clearance is a blocker only when it must already be HELD |
| (uncommitted) | plan executor + facet key fix + live scope verification |

## NEXT SESSION: START HERE
1. **`rescreen-all`** -- the clearance fix reaches nothing until this runs. Expect ~6,000 postings to
   lose the "unreachable" flag and a batch of federal-contractor roles to surface (CACI "Business
   Process Consultant" 93, Guidehouse "Senior Business Process Analyst" 91 were both flagged away).
2. **Partition strategy** for the three boards that are clamped with no country facet -- Booz Allen,
   Leidos, Sentara. Booz Allen's job families are 1,172 / 766 / 445, each under the 2,000 ceiling, so
   it is fully enumerable. The plan executor already supports `partition`; only the plan *builder*
   and the completeness assertion are missing.
   **Acceptance test that is now possible:** after a partitioned pull, assert the union size matches
   the board's `timeType` sum (Booz Allen 2,386). If it comes back 2,000 the partition did not work.
3. **`screens.fit_process` / `fit_technical`** -- schema, scoring in `pipeline.screen`, then a full
   rescreen so all 66k rows carry a lens prediction.
4. **Then the three report lists** (strong process / strong technical / both) with a `lens_source`
   column marking whether each row was placed by the user, the judge, or the model.
5. **VACUUM / defrag** -- the user asked for this; 22,660 postings and 82,734 screen rows were
   deleted today and the file is still ~1.36 GB.
6. **Pending user decision:** record a `user-adjudicated` label on Guidehouse "Senior Business
   Analyst" (see "judge variance" below). He ruled `adjacent`, not bullseye.

## The rescreen trap (established 2026-09-16, worth not re-learning)
`sweep.run` calls `pipeline.daily(since=stats["started"])`, and `_candidate_sql` ANDs that on top of
the rescreen predicate:

```sql
AND (p.first_seen_at >= ? OR p.description_fetched_at >= ?)
```

So on a routine sweep, `rules_version != ?` / `model_version != ?` are **necessary but not
sufficient** -- the row must also have been first seen or re-fetched in that run. New reqs and
changed JDs get the new rules/model; the rest of the corpus keeps its old scores, silently, with no
error. **After any rules or model change, run `rescreen-all` explicitly.**

Changed JD text *is* handled automatically: the upsert bumps `description_fetched_at` only when the
text actually differs, and the screen stage runs after the detail stage.

## Sweep run `bd57bcfd` (2026-09-16, 22.0 min)
137 boards ok, 0 failed, 84,112 live, **7,888 new**, 22 reopened, 4,453 taken down, 5,281 JDs fetched.
Screen: 7,942 rows -> 16 candidate / 68 review.

**1,380 of those take-downs were false** and have been reopened (ids snapshotted outside the repo).
They came from the four clamped boards. One was verified still live on the ATS: Accenture
"Consulting Advanced Degree Consultant - Health" (`strong`, 70). Leidos "Program Financial Analyst V"
(`very_strong`, 87) was a genuine 404. Four Booz Allen rows are unresolved -- the API answers 403
(WAF) and the public page is an SPA shell, so neither proves anything.

## The Workday `total` clamp
Accenture reports `total=2000` against a real count of ~44,187. We were ingesting **4.5%** of the
board and close-passing the rest as taken down. Offsets past the ceiling return page 1 again, so
there is no paginating around it.

**Detection must use a SINGLE-VALUED facet.** The first attempt compared `total` against the widest
facet sum, which is wrong: a posting in three cities counts three times in the location facet, and
`workerSubType` is multi-valued too (Accenture 86,767 against 44,187 postings). That called Autodesk
(405) and Guidehouse (757) clamped when both are complete. `timeType` is one value per posting:

| board | total | timeType | ratio | verdict |
|---|---|---|---|---|
| Accenture | 2,000 | 44,216 | 22.11 | clamped |
| Booz Allen | 2,000 | 2,386 | 1.19 | clamped |
| Leidos | 2,000 | 2,192 | 1.10 | clamped |
| Henry Schein / Autodesk / Guidehouse / GE Vernova | — | — | 1.00 | genuine |

**Probing past the ceiling is NOT a usable test** -- Workday answers any out-of-range offset with
page 1, so even a genuine board looks like it has more. Do not re-try that approach.

## `board_facets` / `board_scope` and the plan executor
Ask each board what it can filter by; never hardcode a facet id. Two tables: `board_facets` (every
facet parameter, nested group, value id, descriptor, count) and `board_scope` (the resolved
strategy). `backend/ats/facets.py` discovers and resolves; `finder`/sweep passes the scope into
`adapters.list_jobs(row, scope=...)`.

**The pull is a plan executor**, so every strategy is one code path with a different plan:
`plain` = one unfiltered pull, `country` = one filtered pull, `partition` = one pull per facet value
unioned on the req key, `truncate` = pull what we can and block the close-pass. Adding `partition`
is a plan *builder*, not a new pull mechanism.

**Three tenant behaviours, and only a live probe tells them apart:**
- applied correctly (Accenture)
- rejected with HTTP 400 (Booz Allen, Sentara -- they expose no country facet at all, only a flat
  city list)
- **accepted and silently ignored** (GE Vernova returned an unchanged total and French locations)

So `verify_scope` applies the facet for real and keeps it only when the total actually drops.

**The filter key is not the tree's parameter name.** Workday nests countries under
`locationMainGroup` -> "Country", but you filter on **`locationCountry`**. Filtering on
`locationMainGroup` answers HTTP 400. Tenants exposing a top-level country parameter
(`Location_Country`, `LocationCountry`, a custom `CF_-_REC_-_...` field) use that name directly.

US matching is by **exact descriptor**, never substring: `"United"` also matches United Kingdom and
United Arab Emirates, both live in Accenture's own country list.

## The corpus is US-only now
**22,660 non-US postings and 82,734 screen rows deleted** (101 MB of JD text). 88,947 -> 66,287.

Guarded: anything carrying an LLM grade, a decision or a `label_docs` row survived (710 rows),
preserving **823 graded labels including 25 process-bullseye and 61 process-adjacent**. NULL-country
rows (8,216) were left alone -- unknown is not non-US. Identifiers backed up outside the repo.

Accenture's board is 86% India (38,911 of 45,219); US is genuinely ~731. That is where the deleted
volume came from, and the `country` strategy is what stops it coming back.

**SQL trap:** the first delete predicate used `NOT IN (SELECT posting_id FROM tracker)` and **all 336
tracker rows have NULL `posting_id`**, which makes `NOT IN` return zero rows for everything. Use
`NOT EXISTS`. Also note the tracker matches by fuzzy name, not posting id, so it guards nothing --
`llm_labels` and `decisions` are what actually protect the user's history.

## Per-lens fit models (sprint plan 18.8) -- zero tokens, trained from existing labels
`vw_label_set_process` / `vw_label_set_technical` mirror `vw_label_set` but carry that lens's grade
and admit only rows judged on it. Shared sources (vault documents, decisions) stay in both: they
describe the candidate, not a lens. `train(lens=)` stores under `kind='tfidf_lr_<lens>'`;
`latest_row(lens=)` asks for one by name.

| | process `c80d6fb39bc7` | technical `3fee819b2a64` |
|---|---|---|
| pos / neg | 1,358 / 3,411 | 985 / 3,784 |
| CV AUC | 0.951 | 0.951 |
| P@20 | 1.00 | 0.98 |
| bullseye/adjacent/stretch/wrong | .80 / .68 / .51 / .22 | .79 / .64 / .43 / .19 |

The real evidence is the vocabularies, which came out genuinely distinct: process leads with
project / governance / change management / transformation; technical with analytics / finance /
dashboards / forecasting / bi. `auc_vs_stretch` (0.776 / 0.794) is NOT comparable to the single
model's 0.836 -- each is judged against its own lens's labels.

## Clearance: held vs obtainable (user ruling, high impact)
> "Any req that has the word OBTAIN means they might be willing to pay for it and fund it so that is
> NOT a blocker. But if they require it be possessed already and active that is the blocker."

He held a federal Public Trust in 2021. Measured over the 11,325 postings carrying the old flag:
**5,300** require a held or unsponsored hard clearance, **3,859** say "ability to obtain", and
**2,165** matched nothing but a compensation paragraph (*"...skill sets, experience, security
clearances, licensure..."*). So ~6,000 were flagged away over language that is not a requirement.

It was costing exactly his lane: CACI "Business Process Consultant" (93), Guidehouse "Senior Business
Process Analyst" (91), "Senior Financial Transformation Consultant" (89), "Business Process Analyst
(Finance)" (86), "Change Management / Communication Lead" (86).

Now: held/current language, or a hard level (TS/SCI, Top Secret, Secret, polygraph) with no offer to
sponsor -> unreachable. "Ability to obtain" at **any** level -> reachable. Boilerplate -> nothing.

## Judge variance is real -- correcting an earlier claim
Guidehouse posts the same "Senior Business Analyst" as **two reqs, 43463 and 43549**, whose JDs are
**99.994% identical (they differ by one period)**. Same rubric version, same scorer, different batch.
They were graded differently:

| | 43463 | 43549 |
|---|---|---|
| overall | stretch | adjacent |
| process | adjacent | **bullseye** |
| technical | wrong | stretch |

The model scored both identically (70, fit 0.753) -- the variance is entirely in the judge. So
"the same JD and rubric produce the same grade" is **false**, and re-grading is not pure waste.

Across 85 near-duplicate graded groups (same employer + title + pay), **21 (25%) show the judge
disagreeing with itself.** Caveat: same employer/title/pay does not guarantee identical text, so 25%
is an upper bound; the Guidehouse pair is the clean proof.

**The user adjudicated it himself and sided with the LOWER grade** (`adjacent`): the process
components are strong, but the role is heavy on requirements documentation and user stories, which
he has not done much of outside ~1 year as a scrum master. Worth recording as `user-adjudicated`.

Related record gap: he *is* writing product requirements now -- Forester, Meridian, jobsearch, in
agentic AI-assisted development -- and none of it is in the evidence the judge reads.

Also: duplicate reqs are stored as separate postings, which inflates the corpus and splits their
grades. Deduping near-identical JDs per employer is a small separate win.

## Carried over
- SmartRecruiters / Workable JD backfill; daily schedule; long-tail adapters (iCIMS, Dayforce,
  Radancy, BrassRing); registry "VERIFY" rows; aggregator keys.
- Cleanup of `db/jobsearch.duckdb.v1-backup-20260915` and the history bundle.
- Coverage/Phase 3b is still blocked and unchanged -- `vw_hard_negatives` can now draw on 1,361
  graded `wrong` rows instead of 7 audited ones, so re-calibrate before deciding.
- `rubric_local.py` is gitignored; its backup is vault `Tools/Finder_Build_Personal_Appendix.md` §2,
  synced at `897123f3fc93`. Re-sync whenever the rubric changes.

## Run
```bash
.venv/bin/python -u sweep_ats.py                 # all stages; --no-report to skip the vault file
.venv/bin/python finder.py rescreen-all          # REQUIRED after any rules/model change
.venv/bin/python -m pytest -q                    # 103
```
