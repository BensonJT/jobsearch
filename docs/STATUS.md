# Session Status — Jobsearch

_Last updated: 2026-09-15 18:00 EDT (Claude Code / Opus on Vostro). Overwrite at the end of each session; git history is the changelog._

## Active Sprint
@/docs/SPRINT_PLAN.md — **Built and committed locally (not pushed): Phase 1, Phase 2, amendments §13 (labels, source invariance, level, workplace, non-US) and §14 (content-first scoring + fixes). Written, not built: §15 (Phase 3 = requirement coverage against the user's evidence; Phase 4 review ledger; public-user context design). Next: Fable audit (below), then build Phase 3 per §15.** Personal values live in the vault's `Tools/Finder_Build_Personal_Appendix.md` (§1 profile, §2 rubric, §5 evidence sources) and gitignored `backend/profile_local.py`.

## Fable audit request (2026-09-15 evening; tokens permitting, else next day)
1. **Phases 1–2 as built** against §11, **as amended by §13 and §14**: read this file, run `.venv/bin/python -m pytest -q` (63), `finder.py shortlist --days 30 --n 30 --db db/finder_scratch.duckdb`, the eyeball SQL in the sections below and in git history of this file, and diff `backend/profile.py` against §5/§13/§14.
2. **§15 as a spec for Phases 3 and 4, before any code** (read the Decision trail below first): is requirement coverage the right content signal; are the requirement classes (level / logistics / domain excluded), the calibration method and the coverage gate sound; is the Phase 4 ledger (Gemma daily with RPM/TPM throttling; Claude Code batch export/import for the backlog; never re-review a (JD hash, rubric) pair) complete; does §15.6 make the repo usable by a stranger without leaking the owner's context.
3. Personal-data check: `git grep --untracked -n -i -E -f .personal_patterns -- . ':!.personal_patterns' ':!LICENSE'` empty.

All numbers below are from **`db/finder_scratch.duckdb`** (E:, gitignored; 77,777 active / 69,618 with a JD). It carries `label_docs`, model **`c1f56157feaf`**, and screens under rules **`a844b0d2d80d`** · model **`c1f56157feaf`** (earlier screens under `823be4a70f67` (§13) and `a78e37bd2f70` (§14 before the fixes) remain in `screens` for comparison). scikit-learn 1.9.1 / numpy / scipy / joblib are installed in `.venv`.

## State of the machine (18:00)
- **Nothing running** (checked 18:05). Oracle all-titles, Workday prefiltered and Workday all-titles JD backfills `=== DONE` 14:18; Amentum ingest `=== AMENTUM DONE` 15:03 (2,768 postings, 2,763 JDs). The live `db/jobsearch.duckdb` is free.
- **Live DB JD coverage: 80,276 active, 78,655 with a JD (98.0%).** Workday 58,616 / 99.3% · Oracle ORC 15,650 / 99.6% · Greenhouse 3,882 / 100% · SmartRecruiters 1,104 / **5.1%** · Lever 506 / 100% · Ashby 393 / 100% · Workable 123 / **0.8%** · BambooHR 2 / 100%. SmartRecruiters and Workable were not in today's backfill (a `--platform smartrecruiters` / `--platform workable` detail pass is the follow-up). 19 runs logged today; last JD fetched 15:02 EDT. `screens` on the live DB: 0.
- **The live DB has not had a finder run yet.** Every number in this file is from `db/finder_scratch.duckdb` (copied 12:30, before the backfill finished and before Amentum). First live run when wanted: `finder.py labels --report` → `train --report` → `rescreen-all` (~7.5 min local disk; slower on E:) → `sync` → `report`. From then on `sweep_ats.py` runs the finder stage itself.

## Decision trail — how ranking moved from titles to context (read this first)
The goal all day: rank postings by how well the JD fits the user's background. Each fork below is a finding on the scratch DB, the user's decision, and what it led to.
1. **Phase 1 (rules only).** The title decided everything: only 1,184 of ~78k active rows had a function term in the title, 264 survived, and rules-only scores topped out at 65, so no posting could reach `strong`.
2. **Phase 2 (TF-IDF + LR on the user's labels).** 5-fold AUC 0.985, but two flaws surfaced. (a) **Negatives were wrong in kind**: vault `pass` / `not-pursuing` folders and passed rows were used as negatives, yet the user explained a JD that reached the vault usually had great-fit language; the doubt was nuance. (b) **Source artifact**: positives were vault-pasted JDs and negatives were career-site pages, so the model learned page boilerplate (`benefits`, `candidate`, `xa` from `&#xa;`) as "not a fit"; State Street's Global OpEx Lead scored 0.28 for that reason and because every State Street doc in training was a pseudo-negative.
3. **§13 (user decisions).** Vault docs are never negatives; negatives are pseudo-negatives only. Text normalized, employer names and level / logistics / boilerplate words removed from the model, career-site copies trained with grouped CV (paired source gap 0.20 → 0.15, not closed). **Level** from the most years any requirement line asks plus the pay band (8+ senior, 5–7 mid, < 5 junior); "associate" never implies level (Associate Director is senior at one employer). **Non-US** hard reject. A JD's stated in-office days beat the "posted in 3+ states = remote" guess (State Street was hybrid in Quincy MA and six other cities, not remote and not DC). Rule score rescaled to 0–100.
4. **The title question.** 10,198 active postings rejected on title alone; 865 of them had fit ≥ 0.5 (Humana Portfolio Enablement Lead .97, Phil, Inc Director of Business Operations .94, USAA HR Integration & Planning Principal .92). The user: titles mislead in both directions, and location, pay band and years are strong signals too. Considered and rejected: counting search keywords in title + JD (that is what TF-IDF already does, and it has no context).
5. **§14 (user-set weights).** Content 50 · level 20 · location 15 · pay 10 · title 5; pay not posted 60 (senior pay is often unposted and only a screen reveals the band), commutable hybrid 80 / on-site 70. With a scored JD the title no longer rejects; fit < 0.35 rejects instead.
6. **The precision problem.** §14 filled `strong` with 377 rows, 334 with no function term in the title: remote senior roles max out level, location and pay (profile ≈ 90), so middling fit still reached `strong`, and the model scores CVS "VP & COO, Medical Affairs" .93 because it shares the vocabulary. Simulated and set aside: **multiplying** fit × profile (cuts the queue to 62 but does not fix the order at the top) and **gating bands on fit**. Set aside by the user: **weighting negative words** (a word negative in one context is not in another; an unfamiliar industry asking for familiar work is a fit).
7. **Bugs found on the bullseye** (Henry Schein R134977, which the user called an outstanding fit): "10 or more years" was not parsed (level scored 60) and pay-related flags double-penalized components. Fixed: 83 → **96, rank 1**. The context problem remains directly behind it (CVS COO 93, Centene Sr Dir Medical Economics 92, Novartis Dir AI Foundations Engineer 90).
8. **§15 (spec, not built).** The fit model counts words; context lives in sentences. **Phase 3 = requirement coverage**: split each JD into requirement / responsibility lines and match each by meaning (sentence embeddings) against the user's evidence (resume bullets, duty statements, SOAR stories, bio, LinkedIn PDF, method document, articles, profile site; paths in the vault appendix §5), reporting "N of M covered" with the gaps named; industry is never a gap by itself. **Phase 4 = LLM review** with a ledger so nothing is reviewed twice: free Gemma under RPM/TPM limits for daily new rows, Claude Code batch files on the user's subscription for the backlog. **§15.6** makes context configuration so a stranger can use the repo without the owner's data.

## §14 content-first scoring — what changed (user decision, 2026-09-15 ~16:00)
- Weights (`SCORE_COMPONENT_WEIGHTS`): **content 50 · level 20 · location 15 · pay 10 · title 5**. Points: level senior 100 / mid 50 / not stated 60; location remote 100 / commutable hybrid 80 / commutable on-site or unstated 70 / nationwide unverified 60; pay band top at ask 100 / at floor 75 / not posted 60 (unposted is unknown until a screen); title tier 1 100 / tier 2 70 / tier 3 50 / none 30 / off-lane 0.
- `screens.rule_score` = the **profile score** (level, location, pay, title on 0–100). Final = 0.5·content + 0.5·profile; no content → profile capped at 60; minus 5 per flag (cap 25); tier-3 cap 80; LLM blend last.
- **Content gate:** with a scored JD, `off-function title` / `off-lane title` no longer reject (off-lane becomes a flag); fit < 0.35 → reason `content does not fit`; fit < 0.50 → flag `content fit borderline`. No JD or no model → the title gate stands.
- `RULE_POINTS`, `SCORE_WEIGHTS`, `rule_points`, `rule_max` removed. Fit stanza reads `profile N · fit x · …`. **Tests: 61 passing.**

## §14 fixes — found on Henry Schein R134977 (17:00)
- **Years parser** missed "Typically 10 or more years of progressive experience", so the bullseye scored level "not stated" (60). `required_years` now reads "10 or more years", "15 years or more of experience", "a minimum of ten (10) years", "at least eight years'", "five to seven years", "(8) years", "Experience: 12+ years" (number phrase before the year word; "experience" in the same sentence; "18 years old" excluded).
- **Double penalty:** flags a component already prices cost no points (`UNPENALIZED_FLAG_PATTERNS`: ask above band top, local/hybrid, nationwide listing, mid level, few years asked, content fit borderline, faith signal). They stay visible and still send the posting to review.
- Rescreen 451 s under rules `a844b0d2d80d`: candidate 227 · review 1,545 · reject 76,005. Shortlist bands very_strong 57 · strong 465 · partial 1,104 · weak 124. Active rows: `junior level` reasons 21,731 (was 19,303: more years phrases parsed), `mid level` flags 7,567.
- **Henry Schein R134977: rank 1, 96 very_strong** (profile 95: level 100 / location 100 / pay 75 / title 100; fit .97). Then Humana AVP Corp Dev Integration 95 · Amgen AVP AI&D Scaled Ops 95 · CVS VP & COO Medical Affairs 93 · M&T Sr Org Change Mgr 93 · USAA HR Integration & Planning Principal 93 · Humana Portfolio Enablement Lead 93 · Centene Sr Dir Medical Economics 92.
- **Tests: 63 passing.**

## §14 results (scratch DB, rescreen 440 s)
- Verdicts **candidate 43 → 225 · review 184 → 1,570 · reject 77,550 → 75,982**. Transitions: reject → candidate 203, reject → review 1,481; candidate → reject 17, review → reject 99 (all `content does not fit`: mostly Capital One / ICF / Guidehouse / Leidos data engineers, Booz Allen Digital Transformation Specialist / Architect, RTX SAP / Kinaxis data transformation).
- Bands (active): **very_strong 44 · strong 350** · partial 886 · weak 472. vw_shortlist: 1,773 rows, 1,259 at ≥ 50, max 95. Only 1 shortlist row lacks a JD.
- Reason families (active): not remote/outside commute 63,582 · **content does not fit 62,635** · outside the US 20,429 · junior level 19,303 · off-function title **8,135** (was 76,593; now only rows without a scored JD) · comp 7,472 · early-career 5,238 · off-lane title 2,637.
- Rescued at the top (were `off-function title` rejects): Humana AVP Corporate Development Integration & Value Creation 95 (fit .97) · USAA HR Integration & Planning Principal 93 · CVS VP & COO Medical Affairs 93 · Centene Sr Dir Medical Economics 92 · Perficient Sr PM AI Data 92 · Angi Dir Large Pro Operations 91 · USAA HR Enablement Director 90 · Phil, Inc Dir of Business Operations, Client Optimization 89 · QTS Dir Procurement Systems & Analytics 89 · Humana Portfolio Enablement Lead 88.
- Named rows: Henry Schein 83 strong (was 82, rank 1; now below the rescued rows) · M&T Sr Org Change Mgr 88 · Marriott Sr Dir Change Management 83 strong · State Street reject (location) with `content fit borderline (0.50)` flag.
- **Precision concern (for the user):** 24 of the top 30 have no function term in the title. Very-strong is dominated by remote Director/VP/AVP roles with pay not posted or at the ask (profile ≈ 93) and fit .80–.90, several outside the lane (CVS VP & COO Medical Affairs, Novartis Director AI Foundations Engineer, Humana Creative Operations Director, Centene VP Medicare Care Management). The fit model separates "senior corporate knowledge work" from the random corpus well, but not near misses from bullseyes: its negatives are easy. See open questions.

## §13 amendments — what changed (user decisions, 2026-09-15 afternoon)
- **Negatives rethought.** Nothing in the vault is a negative: pass / not-pursuing folders are near-miss positives (weight 0.5); passed rows and `pass` decisions are context only, never trained. Negatives = 1,500 pseudo-negatives (random JDs with no function term in the title). The low-data fit weight (0.15) no longer triggers: 362 positives / 1,500 pseudo-negatives → fit weight back to 0.35.
- **Source artifact.** The first model had learned "career-site page = not a fit": top negative terms were page boilerplate and `xa` (7,689 active JDs store line breaks as `&#xa;`). Fixes: HTML-unescape + NFKC; drop lines with ≥ 2 `BOILERPLATE_MARKERS`; strip the employer's name; letters-only tokens; `MODEL_STOP_WORDS` (level words incl. associate, logistics, boilerplate); `max_df` 0.5; URL/req-matched positives trained on the posting's text; other matched positives trained on both copies with `StratifiedGroupKFold`. **Paired held-out gap (same 43 jobs, vault copy vs career-site copy): 0.20 → 0.15** (0.77 vs 0.62). Not closed; remaining negatives are diffuse page words (date, competitive, commitment, diversity, local). Phase 3 embeddings or JD-section extraction are the next lever.
- **Level.** `required_years` reads every "N years … experience" number; level = the MOST any line asks (≥ 8 senior, 5–7 mid, < 5 junior; > 25 ignored). Junior = reason unless an unambiguous senior title (director, VP, principal, head of, chief) or band top ≥ floor (then flag `few years asked`); mid = flag unless senior title or band top ≥ ask; early-career title (intern, summer associate, entry level, junior) = reason. "Associate" never implies level (screen.py's `below target level` superseded in the finder). The senior rule point comes from this level.
- **Workplace.** A JD stating in-office days per week / fully on-site sets `workplace_type` when the ATS left it NULL; stated hybrid/onsite is never "remote" (the ≥3-states guess used to override it — State Street's bug).
- **Outside the US** hard reject (ATS country code, or every location segment names a `NON_US_TERMS` place; one US segment keeps it; bare "Remote" never rejects).
- **Rule score rescaled** to 0–100 against `rule_max()` = 65.
- HTML entities are also decoded before the rules run and in the report's JD body.
- **Tests: 60 passing.**

## §11 results after §13 (scratch DB)
- `labels --report`: 410 positives with text (application 297, decision 45, escalated 68) · 1,500 pseudo-negatives · 356 context-only rows · 1,862 training docs after dedupe (+43 career-site copies).
- `train --report`: **5-fold grouped AUC 0.980** · precision@20 1.000 · positives mean fit **0.79 held-out** / 0.89 in-sample · confusion@0.5 tp 369 / fp 80 / fn 36 / tn 1,420. Held-out by text source: vault 0.82 (n 348) · near-miss folders 0.80 (15) · career-site 0.63 (14) · paired 0.77 vs 0.62 (43). Signal AUCs: rule 0.853 · fit 0.977 · blend 0.608 (rejects score 0).
- Top positive terms: transformation, strategic, analytics, data, change management, initiatives, operational, governance, improvement, project management, process improvement, lean, business process, sigma, business operations, excellence. Top negative: customer, sales, security, date, software, maintenance, guest, electrical, compliance, equipment, safety.
- Highest pseudo-negatives (unlabeled that read like fits): GE Vernova Plant Leader .86, Capital One Sr Mgr Data Analyst Risk .85, Amgen S2P SOX & Compliance .85, GE Vernova Compliance Innovation & AI Lead .84, Fannie Mae Sr Dir Modeling & Analytics .82.
- `rescreen-all`: **452 s**. Verdicts candidate 43 / review 184 / reject 77,550 (was 73 / 193 / 77,511). Bands **strong 11** / partial 42 / weak 68.
- **Default report bar now reaches strong:** vw_shortlist has 6 strong rows (max final 82). The default-bar `report` on scratch still wrote 0 blocks because all 6 were already in `surfaced` from the earlier test reports (14-day exclusion; they appear in the summary table as `(shown …)`). On the live DB, which has no surfaced rows, they would be blocks.
- Reason families (active): off-function title 76,593 · not remote/outside commute 63,582 · off-lane title 22,694 · **outside the US 20,429** · **junior level 19,303** · comp 7,472 · **early-career title 5,238**. Tiered flags: clearance 249 · **mid level 205** · local/hybrid 189 · **few years asked 30**. Only 14 tiered rows reject on outside-the-US alone.
- **Max required years over 69,618 active JDs:** none stated 29,674 · < 5 21,059 · 5–7 9,561 · 8–9 3,988 · 10–14 4,504 · 15–19 738 · 20–25 94. Highest seen: 25 (8 JDs, e.g. TS/SCI system engineer roles), 20 (76), 18 (60).

## §11 eyeball after §13
| Row | Result |
|---|---|
| Henry Schein R134977 | **82 strong**, rank 1, rule 69, fit .97, review (flag: ask above band top). |
| Top of vw_shortlist | 82 Henry Schein · 76 Amgen AVP AI&D Scaled Ops & Transformation (fit .93) · 73 QTS GPO Capital Delivery · 73 M&T Sr Org Change Mgr · 71 QTS GPO Capacity (flag mid level, 7 yrs) · 70 Perficient Dir OCM · 69 McKesson Sr BI & Automation Analyst (T3) · 67 Angi Principal Analytics Eng · 66 Centene Dir Provider Data Process Owner · 65 Freddie Mac Strategic Transformation AI Sr Lead. |
| State Street Global OpEx Lead | fit **.28 → .50**, rule 69, **reject on location** (hybrid 2–4 days/week in Quincy MA / Boston / Princeton / Irvine / Austin / Atlanta / Sacramento; the listing never says DC). |
| Marriott Sr Director, Change Management and Associate Engagement | was rejected as "below target level (associate)"; now **review 62 partial**, fit .97. |
| Honeywell Director Operational Excellence (x3) | reject: plant-floor scope + not commutable; "Director Operational Ex" also outside the US (MX). |
| Amgen FP&A Manager (Shanghai) | reject: outside the US (CN). |
| Phil, Inc Director of Quality Excellence | still reject on `off-function title` only (fit .90): the title gate question below. |
| Junior / early-career on tiered rows | Summer Associate internships (early-career), Process Optimization Specialist (max 3 yrs), Sr Associate Data Analytics (max 3 yrs, IN). |

Eyeball script: `SELECT` families over `vw_screen_latest` joined to active postings (as in the Phase 1/2 blocks in git history), plus `rules.required_years(html.unescape(description_text))` over every active JD for the years distribution.

## Open questions / decisions
- **Context, not vocabulary — decided 17:30: build requirement coverage as Phase 3 (§15), LLM review as Phase 4; negative-word weighting set aside (a word negative in one context is not in another).** Evidence sources confirmed by the user and listed in the vault appendix §5. The TF-IDF model scores shared vocabulary (transformation, governance, change management), not context, so senior roles in other functions score .85–.93 (CVS VP & COO Medical Affairs, Novartis Dir AI Foundations Engineer). Proposed: **requirement coverage**, which splits a JD into requirement / responsibility lines, matches each by sentence embedding against evidence of the user's background, and reports "N of M matched, unmatched: …" as the main content signal (the `jd_bucketize` coverage idea at search time). Evidence source to confirm with the user: master bullets + contexts in the local `resume` DB, `Bio_Jeff_Professional.md`, the Signature Method document, pursued JDs (read at run time from vault / local DB, never copied into the repo). Plus the Phase 4 LLM rubric read on the top 30–50. The TF-IDF model stays as the cheap 0.35 content gate. Multiply-blend idea set aside (it fixes volume, not context).
- **§14 precision (earlier framing).** 394 strong-or-better rows is more than a review queue can hold, and the top is crowded by senior generalist roles the model reads as fits. Levers, none built: (a) **function-coded pass decisions**: `finder.py mark <id> pass --reason function` counts as a content negative, while nuance / logistics passes stay context only (honours §13: a vault JD is never a negative, but an explicit 'wrong function' is); (b) **harder pseudo-negatives**: sample senior corporate postings with no function term instead of the whole corpus; (c) **Phase 3 embeddings**: similarity to the jobs actually pursued, averaged into content; (d) raise the strong bar for tier-less titles, or give the title more than 5%.
- ~~Title gate~~ — replaced by the §14 content gate.
- **Paired source gap 0.15** remains (see above).
- **Blend AUC 0.608** is expected (rejects score 0); §6 weights still untuned.
- **Peraton (iCIMS) — feasibility checked 15:10, not built.** Every `*.icims.com` URL (Peraton, Cadmus, Girl Scouts, HarperCollins) returns an AWS WAF captcha (HTTP 405), so a generic iCIMS adapter is not possible from the shell. Peraton's own Webflow site exposes all **1,458 jobs** through a public Typesense search index (JSON, 250/page, 6 requests; key + host scraped from `www.careers.peraton.com/search-jobs` at run time): title, req id, primary location, workplace (on-site 1,183 / hybrid 180 / remote 95), pay text, full JD (responsibilities + qualifications HTML). `datePosted` only from the per-job page's JSON-LD. Estimate ~½ day as a `typesense` platform adapter. Registry row today: `Peraton,icims,…,unresolved` (listed twice). Decision for the user: build it or not.

## Phase 2 — what was built (before §13; carried for the audit)
- `labels.py` (vault loaders, posting match, pseudo-negatives, sync_labels), `features.py` (TF-IDF + LR, CV, hard negatives, top terms, load_latest), pipeline model integration, `finder.py labels` / `train`. Phase 2 deviations 1–8 from the first build are superseded where §13 differs (labels, dedupe priority still holds, low-data rule).

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
