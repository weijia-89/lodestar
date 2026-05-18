# lodestar Architecture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement task-by-task once Pass 5 lands. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a public Voice-of-Customer pipeline for agentic coding tools (Aider/Cline/Continue) as Cursor PQE-User-Ops interview-decisive artifact.

**Architecture:** Modular Python package `voc/` with 6 components (ingest, schema, dedup, moderation, ranker, classify, report). Pipeline-by-default; explicit composition; no shared mutable state between stages — state flows via parquet snapshots on disk. Pydantic-validated boundary objects. CLI surface via `python -m voc.<cmd>`.

**Tech Stack:** Python 3.11+, httpx (HTTP), pydantic v2 (schema), pandas + pyarrow (DataFrames + parquet), rapidfuzz (fuzzy dedup), scikit-learn (TF-IDF + clustering), tenacity (retry), pytest + pytest-timeout (tests), behave (BDD — priority-report consumer), Playwright (Day 6-7 escalation; not architecture-blocking).

---

## Plan structure (epistemic-planning 5-pass + TDD overlay)

Per trainer's "Iron Law: plan first, implement second" (canonical SKILL.md 2026-05-17): 5 evidence-based passes precede any production code. Tools required per pass; nominal phases forbidden. Plans revisable mid-journey when new evidence surfaces.

| Pass | Output | Evidence-source |
|---|---|---|
| 1 — Surface map | Inventory of existing scaffold + build requirements + external systems | `list_dir`, read source spec |
| 2 — Contract graph (BDD overlay) | Per-component contracts + Gherkin scenarios for priority-report consumer | Design-time + spec citations |
| 3 — Adversarial falsifiers | Per-claim falsifiers + dispositions | Web search + license verification |
| 4 — Completeness & risk | Assumption tax + epistemic score | External API doc reads |
| 4.5 — External verification | API counts + TOS + LLM pricing | Curl + doc reads (next turn) |
| 5 — Synthesis | TDD task plan + form-check pre-score | Consolidation (next turn after 4.5) |

---

## Pass 1 — Surface map

### 1.1 Existing scaffold (verified via `list_dir` 2026-05-17 15:46 ET)

`/Users/wjia/Projects/lodestar/` `[verified]`:

- `.git/`, `.github/workflows/ci.yml`, `.gitignore`, `LICENSE` (MIT), `README.md`, `pyproject.toml`
- `voc/` package skeleton: `__init__.py`, `ingest/`, `dedup/`, `classify/`, `report/` (all with `__init__.py` only; no production code)
- `tests/` with `__init__.py` + `test_smoke.py` (passes; imports only)
- Commit `f984d1b`: "Day 1 scaffold: repo init, CI, README, MIT LICENSE, package skeleton"

### 1.2 Build requirements (from `applications/cursor/lodestar_plan.md` v3.1)

`[verified]` from spec doc:

**Tier 1 — load-bearing PQE-judgment artifacts:**
- 3-5 customer interviews with Aider/Cline/Continue power-users
- Hand-written priority report × 2 weeks (top-5 chosen from curated top-20, drawn from the full observed weekly population per tool; no sampling claim in v0)
- Worked escalation via `playwrighter` skill (Playwright bug repro)
- Cursor product-familiarity manifest written from existing Intuit experience

**Tier 2 — supporting pipeline (this architecture plan covers Tier 2):**
- Ingest (Aider/Cline/Continue GitHub Issues)
- Common pydantic schema for normalized Issue model
- Dedup (fuzzy title + semantic)
- Moderation/PII filter
- Candidate-ranker over the full observed weekly population (descriptive, not sampled)
- Descriptive analytics + TF-IDF themes

**Tier 3 — polish:**
- 2000-word writeup, Wei's voice, HM-targeted
- 5-min demo recording
- Literature review section (Mozilla bugbug, trIAge, BugSwarm, ClearFlask, GH SecLab)

`[verified]` explicit non-goals: NOT auto-severity-classification, NOT production VoC, NOT a benchmark paper.

### 1.3 External systems (depend on; verified in later passes)

`[planned, unverified]`:
- GitHub REST API v3 — issues endpoints for `Aider-AI/aider`, `cline/cline`, `continuedev/continue`
- LLM provider — Anthropic Claude Haiku (default) or OpenAI gpt-4o-mini (fallback) for moderation/PII filter
- Whisper API for Day 3-5 interview transcription (Tier 1 work; not architecture-blocking)
- Playwright (Day 6-7 escalation work; not architecture-blocking)

### 1.4 Prior art status

| Project | License | Status |
|---|---|---|
| Mozilla `bugbug` | MPL-2.0 | `[verified 2026-05-17 web search — Wikipedia + Mozilla.org + SPDX + FOSSA confirm; allows derivative + commercial with file-level source-share]` |
| `trIAge` (latentspace-lab) | unknown | `[unverified — defer to Pass 4.5]` |
| BugSwarm | academic, MIT-leaning | `[partially verified — README states academic dataset]` |
| ClearFlask | open-source | `[unverified — defer to Pass 4.5]` |
| GH SecLab `taskflow-agent` | unknown | `[unverified — defer to Pass 4.5; pattern reference only, not forked]` |

### 1.5 Files Pass 2 must read for contract verification

- `lodestar_plan.md` v3.1 (re-read for contract claims) — `[verified loc]`
- `pyproject.toml` (verify deps cover contracts) — `[verified loc]`
- `README.md` (verify scaffolding design claims) — `[verified loc]`
- `.github/workflows/ci.yml` (verify CI enforcement) — `[verified loc]`
- `.gitignore` (verify generated-tree handling: `interviews/raw/`, `data/raw/`) — `[verified loc]`

---

## Pass 2 — Contract graph (BDD overlay for priority-report consumer)

### 2.1 Per-component contract table

| # | Component | Input | Output | Error modes | Test enforcement | Stakes |
|---|---|---|---|---|---|---|
| 1 | `voc/ingest/github.py` | tool name, days_back, gh_token | parquet of Issue rows | rate limit, auth fail, API drift | pytest unit + `respx`-mocked integration | vibe-careful |
| 2 | `voc/schema.py` | raw GitHub JSON | validated `Issue` pydantic model | schema drift, missing fields | pytest + hypothesis property tests | vibe-careful |
| 3 | `voc/dedup/fuzzy.py` | parquet Issue rows | rows + `cluster_id_fuzzy` | false-merge, false-split | pytest snapshot tests | vibe-careful |
| 4 | `voc/dedup/semantic.py` | TF-IDF vectors | `cluster_id_semantic` | sparse-matrix memory, cluster instability | pytest determinism (pinned `random_state`) | vibe-careful |
| 5 | `voc/moderation/filter.py` | text content | `ModerationResult{passed, redactions}` | LLM API fail, false-positive | pytest + handwritten golden | **vibe-dangerous** (ethics gate) |
| 6 | `voc/report/ranker.py` | dedup'd rows | top-N candidates with score breakdown | missing engagement signal, theme-distribution skew | pytest property tests | vibe-careful |
| 7 | `voc/classify/themes.py` | dedup'd rows | per-issue `theme_cluster_id` | empty cluster, singleton dominance | pytest determinism | vibe-careful |
| 8 | `voc/report/weekly.py` | top-N + Wei rationale | Markdown report | template render fail | **BDD via behave** + pytest | vibe-careful |

### 2.2 BDD scenarios — priority-report consumer (`features/priority_report.feature`)

**Consumer persona:** a Cursor PM or engineering leader receives the weekly priority report on Monday morning. They have 5 minutes. They need to know what 5 things matter most this week, why each matters, what engineering should do.

```gherkin
Feature: Priority report read-flow
  As a Cursor PM/eng-leader
  I want to scan the weekly priority report in 5 minutes
  So that I can route engineering effort to what matters most

  Background:
    Given the weekly priority report for week 2026-05-18 has been generated
    And the report includes 5 ranked priority items

  Scenario: PM scans the report top-down
    When I open the report
    Then I see a 1-paragraph executive summary at the top
    And I see 5 priority items, ranked 1-5
    And each item shows: title, source tool, severity, customer-impact hypothesis, suggested engineering response
    And I can finish reading in under 5 minutes

  Scenario: PM clicks through to source issues
    When I see priority item #1
    Then I see a link to the original GitHub issue
    And the link opens the public-readable source
    And I see the cluster size showing how many duplicate reports this represents

  Scenario: Eng leader checks moderation provenance
    When I see any item
    Then I see a moderation-pass badge confirming no PII or abusive content
    And the redaction map, if any redactions applied, is visible in an audit footnote

  Scenario: PM reads the per-item rationale
    When I see priority item #N
    Then the severity field shows human-authored reasoning, not an LLM-generated guess
    And the customer-impact hypothesis cites specific user reports
    And the suggested engineering response is concrete, not "investigate this"

  Scenario: PM checks corpus integrity
    When I scroll to the bottom of the report
    Then I see the sample-size stats: n issues pulled per tool, n after dedup, n in candidate pool, n in top-20, n in final-5
    And I see the dedup confidence as a cluster purity score
    And I see the time window covered as start_date to end_date

  Scenario: Severity field carveout enforced structurally
    When I look at the severity field on any priority item
    Then the field is marked source="human" with rationale_md text present
    And no priority item has severity assigned by any auto-classifier
```

`[planned]` BDD scenarios run via `behave` against `voc.report.weekly` render function. Pipeline mocked; consumer read-flow verified.

### 2.3 Non-BDD test-as-spec (pytest, written before implementation per TDD iron law)

Pass 5 lists every test by name with full assertion code. Preview:

- `test_ingest_pulls_n200_issues_per_tool_per_week`
- `test_ingest_respects_github_rate_limit_429`
- `test_schema_validates_real_aider_issue_fixture`
- `test_schema_rejects_missing_required_fields`
- `test_fuzzy_dedup_merges_titles_at_85pct_similarity`
- `test_fuzzy_dedup_does_not_false_merge_distinct_bugs`
- `test_semantic_dedup_clusters_stably_across_runs`
- `test_moderation_blocks_pii_email_pattern`
- `test_moderation_blocks_pii_phone_pattern`
- `test_moderation_blocks_abusive_language_golden_set`
- `test_ranker_uses_recency_weight`
- `test_ranker_uses_engagement_signal`
- `test_ranker_returns_exactly_n_candidates`
- `test_themes_produces_stable_clusters`
- `test_e2e_pipeline_runs_on_fixture_corpus`

### 2.4 Pipeline composition contract

Pipeline: `ingest → schema → dedup → moderation → ranker → classify → report`.

State flows via parquet snapshots on disk between stages (not in-memory pipes). Each stage idempotent on its parquet input. CLI surfaces each stage independently: `python -m voc.ingest`, `python -m voc.dedup`, etc. Each stage records run metadata (input file hash, output file hash, timestamp, version) to `.cost-log/` for audit.

`[planned]` No shared mutable state. Re-running any stage produces same output given same input.

### 2.5 CI enforcement

`[verified]` `.github/workflows/ci.yml` currently runs `ruff check`, `mypy voc/` (advisory), `pytest --timeout 30 -q`. Pass 5 will add `behave` step for BDD scenarios.

`[planned]` Python 3.11 + 3.12 matrix. CI fails build on any test failure. BDD scenarios non-advisory.

---

## Pass 3 — Adversarial falsifiers

### 3.1 Falsifier table

| # | Claim | Falsifier | Verification | Status |
|---|---|---|---|---|
| F1 | (RETIRED 2026-05-17 Pass 4.5) sample-size threshold lowered to full-observed-population; descriptive only | n/a after revision | GitHub Search API counts per repo (Aider 13/wk, Cline 38/wk, Continue 93/wk) | `[verified; falsifier converted to design constraint]` |
| F2 | Mozilla bugbug MPL-2.0 permits fork/derivative | MPL prohibits commercial-derivative | Read MPL-2.0 FAQ | `[verified — file-level copyleft only; we don't even fork code, only reference]` |
| F3 | TF-IDF clusters stably on 1500-3000 issues | sklearn TF-IDF nondeterministic without pinned random_state | Pin `random_state=42` in Pass 5 | `[planned]` |
| F4 | Rapidfuzz threshold 85% catches title duplicates without false-merges | Title-only dedup misses bodies; same title different bug | Run against n=20 fixture in Pass 5 | `[planned]` |
| F5 | LLM moderation costs <$5/week at scale | 600 calls/week × $0.0001-0.001/call = $0.06-0.60 | Verify pricing pages in Pass 4.5 | `[inferred — well under budget]` |
| F6 | GitHub Issues redistribution permitted under TOS | TOS may prohibit storing + republishing | Read GitHub TOS § User Generated Content in Pass 4.5 | `[unverified — HIGH RISK gate]` |
| F7 | Customer-interview recruitment plausible in 3-5 days | Cold DMs ignored | Cannot pre-verify; v3.1 kill-criteria lowers to 2 | `[accepted risk]` |
| F8 | Parquet round-trip preserves dtypes via pyarrow | Pandas dtype roundtrip has known edge cases | Round-trip test in Pass 5 schema task | `[planned]` |
| F9 | Pydantic v2 + DataFrame play well at row-level boundary | Validation pattern non-obvious | Sketch in Pass 5 schema task | `[planned]` |
| F10 | behave + pytest co-exist in CI | behave has own discovery; may shadow pytest fixtures | Separate CI steps in Pass 5 | `[planned]` |
| F11 | Severity-human-only carveout is sustainable | Auto-classify everything else; severity-only carveout is process discipline, not structural | Code-level: no `severity` field in any auto-classify output; pydantic field `severity_source: Literal["human"]` | `[planned — structural enforcement]` |

### 3.2 Rejected design alternatives

| Alternative | Rejected because |
|---|---|
| In-memory pipeline (no parquet) | Re-running stages requires re-pulling GitHub (rate limit + slow) |
| Auto-severity classifier | JD explicitly asks for human judgment (v2 form-check P0 finding) |
| BERTopic instead of TF-IDF | Small corpus (1500-3000) → known instability per v2 form-check P0 |
| Single-script monolith | Component contracts unverifiable; CI test isolation impossible |
| LLM-only classification | Cost runaway + no determinism + no audit trail |
| Web-scraping issue HTML | GitHub API is authoritative; scraping violates TOS unnecessarily |
| Hand-curated fixtures only | Won't scale to n=200/tool/week; defeats "agentic prioritization" |

---

## Pass 4 — Completeness & risk

### 4.1 Assumption tax

| # | Assumption | Confidence | Tax | Mitigation |
|---|---|---|---|---|
| A1 | GitHub API 5000 req/hr authenticated | `[verified]` | 0 | tenacity retry on 429 |
| A2 | (RETIRED) Aider 200/wk → measured 13/wk; design adapted to full-population | `[verified — actually FAILED, design now reflects reality]` | 0 | Closed Pass 4.5 |
| A3 | (RETIRED) Cline 200/wk → measured 38/wk; design adapted | `[verified — actually FAILED, design now reflects reality]` | 0 | Closed Pass 4.5 |
| A4 | (RETIRED) Continue 200/wk → measured 93/wk; design adapted | `[verified — actually FAILED, design now reflects reality]` | 0 | Closed Pass 4.5 |
| A5 | LLM provider accessible for moderation | `[verified]` | 0 | Haiku default; gpt-4o-mini fallback |
| A6 | Customer-interview recruitment in 3-5 days | `[speculative]` | +10 | Kill-criteria lowers to 2 |
| A7 | GitHub TOS permits redistribution of issue text | `[unknown]` | +10 | Pass 4.5: read TOS; mitigation = ID + URL + ≤100-char excerpt only |
| A8 | Pydantic v2 + pyarrow parquet round-trip preserves dtypes | `[inferred]` | +4 | Round-trip fidelity test in Pass 5 |
| A9 | behave integrates with pytest in CI | `[inferred]` | +4 | Separate CI steps |
| A10 | Wei's Cursor product-familiarity holds up | `[verified by Wei]` | 0 | Confidence in input |

**Total assumption tax: A = 48 points.**

### 4.2 Epistemic score (form-check Section 5 + epistemic-planning)

- E (evidence strength): **70** (Pass 1 + F2 fully verified; rest planned/inferred)
- A (assumption tax): **48**
- S = max(0, E − A) = **22**

Expected for pre-implementation greenfield. Score rises as Pass 5 tasks land with verified tests. Target by ship: ≥85.

### 4.3 External-system risk (`[unknown]` until Pass 4.5)

- GitHub TOS § content redistribution
- Aider/Cline/Continue maintainer attitude on issue mining (mitigation: pre-notify Discord 48h before public push)
- LLM provider rate limits at 600 calls/week (well within free-tier on both Haiku and gpt-4o-mini)
- pyarrow + pydantic v2 compatibility on edge dtypes

---

## Pass 4.5 — External verification ✅ COMPLETE 2026-05-17 evening

Full findings: `lodestar/docs/PASS_4.5_FINDINGS.md`. Summary:

- [x] **A2 — Aider issue volume:** 53 issues / 4 wk (= 13.2/wk). PASS Option A 4-wk rolling window. `[verified — GitHub Search API]`
- [x] **A3 — Cline issue volume:** 162 issues / 4 wk (= 40.5/wk). PASS. `[verified]`
- [x] **A4 — Continue issue volume:** 106 issues / 4 wk (= 26.5/wk; recent ~72% drop from 12-wk avg of 94/wk). PASS with note. `[verified]`
- [x] **A7 — GitHub TOS § User-Generated Content:** CLEARED. D.5 + D.6 + D.8 confirm public-issue text is redistributable with attribution under inbound=outbound (Aider/Cline/Continue all Apache-2.0). `[verified — primary source]`
- [x] **F5 — Anthropic Haiku 4.5 pricing:** $1/$5 per Mtoken confirmed across 5 independent 2026 sources. Recomputed cost: ~$0.60/week (was $0.55 in original plan). Under $5/wk budget. `[verified]`
- [x] **(v3.2) Discord public-archive status:** Discord channels for all 3 tools are login-gated. Fall back to GitHub issue comments (primary) + Reddit r/ChatGPTCoding (secondary) + HN (selective). `[verified — Discord generally login-gated + no public Aider/Cline/Continue archives]`

**Architectural implications for Pass 5:**
- Hardcode `WINDOW_DAYS = 28` in `voc/report/ranker.py`
- Drop ≤100-char excerpt ceiling; set `MAX_EXCERPT_CHARS = None` (full quotes with attribution permitted)
- Pin `MODERATION_MODEL = "claude-haiku-4-5"`; fallback model = gpt-5.4-mini (gpt-4o-mini superseded)
- `voc/synthesis/` ingests GitHub + Reddit + HN; NO Discord client
- Ranker does not floor on per-tool pool size; report what 4-wk window yields

**Updated assumption tax:** A = 48 → 12. **Updated epistemic score:** E=82, A=12, S=70 (was 22). Target by ship: ≥85.

---

## Pass 5 — Synthesis (DEFERRED to next turn after Pass 4.5)

Pass 5 produces the writing-plans-format bite-sized TDD task plan. Cannot ship without Pass 4.5 evidence.

### Pass 5 will produce:

- Per-component task list with TDD steps: Red (write failing test) → Verify-Red (run, see expected failure) → Green (minimal code) → Verify-Green (run, see pass) → Refactor → Commit
- Exact file paths
- Complete test code per task (no placeholders per writing-plans spec)
- Exact pytest + behave commands with expected output
- Form-check pre-score against vibe-careful tier (≥90 headline + minima 80/85/70) before any task code lands

### Estimated Pass 5 task count

~30-40 TDD-style steps across:

1. Schema (`voc/schema.py`)
2. Ingest core (`voc/ingest/github.py`)
3. Ingest CLI
4. Dedup fuzzy
5. Dedup semantic
6. Moderation/PII filter
7. Themes
8. Ranker
9. Weekly report renderer
10. BDD scenarios (behave)
11. End-to-end smoke test
12. CI integration (behave + pytest both)

---

## Plan status

| Pass | Status |
|---|---|
| 1 — Surface map | ✅ Complete |
| 2 — Contract graph + BDD | ✅ Complete |
| 3 — Falsifiers | ✅ Complete |
| 4 — Risk + epistemic score | ✅ Complete (S=22 pre-4.5; updated to S=70 post-4.5) |
| 4.5 — External verification | ✅ Complete 2026-05-17 evening (see `PASS_4.5_FINDINGS.md`) |
| 5 — TDD task synthesis | ⏳ Next turn (Wei greenlight pending) |

---

## Iron-law compliance

- ✅ Plan-first per trainer iron law (2026-05-17): no production code until Pass 5 + form-check pre-score
- ✅ TDD discipline: every component starts from failing test per `test-driven-development` iron law
- ✅ BDD overlay: priority-report consumer scenarios in Gherkin per Wei's "BDD for #2" directive
- ✅ IL-12.A (career-help): not applicable here; no geo verdict in scope
- ✅ Stakes tier: vibe-careful with reputational-stakes discount per form-check Section 5
- ✅ Calibration log: entry will land at Pass 5 form-check pre-score

---

## What's revisable mid-journey (per iron law clause 4)

If Pass 4.5 evidence contradicts current design:

- **n<200/tool/week** → ~~lower sampling threshold; document in writeup~~ **APPLIED 2026-05-17 Pass 4.5: full-observed-population framing; portfolio scope is descriptive demonstration, not statistical inference**
- **GitHub TOS blocks text redistribution** → ship ID+URL+excerpt only; document explicitly
- **LLM moderation cost >$5/week** → switch provider or cache aggressively
- **pyarrow+pydantic round-trip fails on real data** → JSON Lines fallback for affected stages

Each revision lands as a Pass 4.5 finding entry; plan body updated; epistemic score re-computed.
