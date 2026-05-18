# Prior art

> **Method:** Searches conducted 2026-05-17 via GitHub MCP search + web search + direct repo reads. Evidence tagged per epistemic-planning: `[verified]` = followed link, viewed README/structure content; `[partially verified]` = read repo landing page + search snippets, did not deep-dive code; `[inferred]` = relied on search snippet without read; `[unknown]` = could not verify in this pass. Reads logged in `docs/superpowers/plans/2026-05-17-architecture.md` Pass 4.5.

## Headline finding

**No public artifact does cross-tool customer-voice synthesis for AI-coding tools specifically.** Prior art clusters into five adjacent-but-distinct categories: ML bug classification (Mozilla bugbug), in-thread LLM issue assistants (trIAge), single-repo LLM issue prioritizers (RaschidJFR + several low-star hobby projects), customer-facing intake (ClearFlask), and bug-reproduction benchmarks for program-repair research (Defects4J, BugSwarm, SWE-bench). lodestar sits in the unfilled gap: cross-repo + human-judged severity + weekly external priority report.

---

## Category 1, ML bug classification

### Mozilla bugbug `[verified]`

- **URL:** https://github.com/mozilla/bugbug
- **License:** MPL-2.0 (allows derivative work + commercial use with file-level source-share; verified separately via Mozilla.org + SPDX)
- **Scale:** ~1k stars; actively maintained; Mozilla's CI integrates it
- **Function:** 19+ classifiers on Bugzilla bugs and GitHub issues, including: `assignee`, `backout`, `bugtype` (crash/memory/performance/security), `component`, `defect vs enhancement vs task`, `defect`, `devdocneeded`, `needsdiagnosis`, `qaneeded`, `regression vs non-regression`, `regressionrange`, `regressor`, `spam`, `stepstoreproduce`, `testfailure`, `testselect`, `tracking`, `uplift`. The `defect` classifier reports ~93% accuracy on 2110-bug dataset.
- **Architecture (pipeline pattern):**
  - `bugbug/bugzilla.py` + `bugbug/github.py`, ingest layer
  - `bugbug/bug_features.py`, feature extraction
  - `bugbug/model.py` + `bugbug/models/`, model layer
  - `bugbug/nn.py`, neural network integration
  - `bugbug/nlp/`, NLP utilities
  - `bugbug/db.py`, simple JSON storage
- **What lodestar adopts:** The pipeline pattern (ingest → features → analytics → output). The conceptual credibility that ML/LLM-on-issues at scale is a legitimate engineering discipline.
- **What lodestar diverges from:** bugbug auto-classifies several severity-adjacent things (defect-vs-task, regression-vs-not, bugtype). lodestar deliberately does NOT auto-classify severity, that's the PQE-shape demonstration. bugbug is single-project-centric (Mozilla); lodestar is cross-tool (Aider + Cline + Continue). bugbug uses Keras/scikit-learn classifiers with labeled datasets; lodestar uses descriptive analytics (TF-IDF themes, engagement weighting) without claiming model accuracy.

---

## Category 2, In-thread LLM issue assistants

### trIAge (latentspace-lab) `[verified, README; status: under construction]`

- **URL:** https://github.com/latentspace-lab/trIAge
- **License:** `[unknown, not displayed on landing]`
- **Function:** "AI assistant for open-source communities." LLM responds in-thread to issues, discussions, and PRs.
- **Documented skills (under construction per README):** Support, Issue Quality Control, Issue Triage (categorize / dedup / prioritize / link related), Debugging, Testing (test case generation), Pull Request Review, Documentation, Changelogs.
- **Shape:** Per-issue or per-PR conversational response. Each issue gets analyzed individually; the assistant comments back in the discussion thread.
- **What lodestar adopts:** Validation that LLM-based issue analysis is a recognized pattern in the AI-coding-tools space.
- **What lodestar diverges from:** trIAge is conversational + in-thread; lodestar is batch + analytical + external-report-shaped. trIAge serves the issue submitter; lodestar serves a hypothetical PM/eng-leader downstream consumer. Both projects share "categorize + dedup + prioritize" primitives but apply them at different granularities (per-issue interactive vs cross-issue weekly).

---

## Category 3, Single-repo LLM issue prioritizers

### RaschidJFR/github-issue-analyzer `[verified, README, features, output schema]`

- **URL:** https://github.com/RaschidJFR/github-issue-analyzer
- **License:** `[unknown, not displayed]`
- **Function:** "A Python tool for analyzing and prioritizing GitHub issues with AI based on traction, impact, and estimated effort."
- **Scoring formula (verified from README):**
  - **traction** = `commentCount × 0.3 + commenterCount × 0.6 + reactionCount × 0.15 + avg_comments_per_week × 0.2`
  - **impact** = LLM-judged from conversation context (prompt at `agents/prompts/`)
  - **effort** = LLM-judged complexity
  - **priority score** = `traction × impact / effort`
- **Templates:** "DX" (Developer Experience) and "SDAP" (Security, Durability, Availability, Performance)
- **Output:** CSV with fields `number, url, title, issue_type, summary, traction, impact, impact_analysis, effort, score, createdAt, avg_comments_per_week, commentCount, commenterCount, reactionCount, last_comment`
- **What lodestar adopts:** The **traction formula concept** (weighted engagement signals: comment count, commenter diversity, reactions, recency-of-conversation). lodestar's ranker borrows the structural idea (multi-signal weighted score) while pinning the impact and severity signals to human judgment instead of LLM judgment.
- **What lodestar diverges from:** RaschidJFR's `impact` and `effort` are LLM-judged → lodestar's `severity` is human-judged (PQE shape, per JD). RaschidJFR is single-repo per invocation → lodestar is cross-repo synthesis. RaschidJFR outputs raw CSV → lodestar outputs a weekly PM-consumer-shaped Markdown priority report with Wei rationale.

### Smaller LLM-issue-analyzer projects `[partially verified, read search snippets, did not deep-dive each]`

Five additional single-author projects found via GitHub MCP search:

| Repo | Stars | Created | Pattern |
|---|---|---|---|
| `alexh-scrt/bug-triage` | 1 | 2026-04 | CLI; OpenAI or Anthropic; classify/dedup/prioritize/severity → Markdown or JSON |
| `Shirisha-g08/ai-github-issue-analyzer` | 0 | 2026-01 | Web app; AI/LLM; structured insights |
| `daivikpurani/issue-autopilot` | 1 | 2025-06 | Auto-label/prioritize/assign via Anthropic Claude |
| `Y1L1N10/SmartIssues` | 0 | 2026-02 | CLI + GitHub Actions; Claude/Gemini/GPT; categorize + prioritize + summarize |
| `developer8HARSHAL/Bug-Analyzer-Agent` | 1 | 2025-09 | n8n workflow + OpenAI embeddings + Pinecone vector search + GPT root-cause + Slack |

**Cluster observation:** The space is thinly populated with low-star, single-author, single-repo projects. None do cross-tool synthesis. None do explicit human-severity carveout. None ship a PQE-shaped weekly external report. **lodestar's positioning is empirically defensible as a distinct contribution.**

---

## Category 4, Customer-facing feedback intake

### ClearFlask `[verified, README, architecture]`

- **URL:** https://github.com/clearflask/clearflask
- **License:** AGPL-3.0 (verified via Cloudron forum citation; copyleft applies, network-use triggers source-share obligation)
- **Function:** Customer-facing feedback management tool. Users submit feedback; product teams triage publicly.
- **Architecture (full-stack web app):** OpenAPI between frontend and backend; React + NodeJS Connect server frontend; Java backend on DynamoDB + ElasticSearch + S3 + KillBill billing.
- **What lodestar adopts:** Nothing architecturally (full-stack web app is wrong shape for a portfolio Python analytics pipeline).
- **What lodestar diverges from:** ClearFlask is INBOUND (users submit feedback to the tool); lodestar is OUTBOUND (mines already-public issues; synthesizes for engineering). They're complementary, not competing, a Cursor team could plausibly run ClearFlask for direct customer feedback AND lodestar-style analysis for GitHub-issue voice. Listed here because it's the open-source VoC reference point Wei's writeup will be compared to.

### Adjacent commercial closed-source VoC

Productboard, Canny.io, Aha!, UserVoice, all closed-source commercial; relevant only as landscape reference, no code to read.

---

## Category 5, Bug-reproduction benchmarks (program-repair research)

### Defects4J, BugSwarm, SWE-bench, "GitHub Recent Bugs Dataset" `[partially verified, search snippets + survey paper references]`

- **Function:** Reproducible bug datasets for evaluating automated program repair and LLM debugging agents.
- **Shape:** Downstream of triage entirely, these benchmarks assume the bug is already prioritized and engineering effort is committed; they evaluate whether an LLM can synthesize a patch.
- **Why listed:** Completes the landscape. Adjacent academic survey: `iSEngLab/AwesomeLLM4SE` (SCIS 2025 survey) and `iSEngLab/AwesomeLLM4APR` (TOSEM 2026 systematic review). lodestar can cite as the broader landscape map.
- **What lodestar diverges from:** Entirely different problem. Patch generation is solution-space; lodestar is problem-space (what to work on, not how to fix it).

---

## Synthesis: lodestar's positioning statement

> Cross-tool customer-voice synthesis for agentic coding tools (Aider, Cline, Continue). Adopts the pipeline-pattern architecture (ingest → features → analytics → output) from Mozilla `bugbug` and the multi-signal weighted engagement-scoring concept (variation on traction = comments + commenters + reactions + recency) from `RaschidJFR/github-issue-analyzer`. Deliberately diverges from all prior art on three axes:
>
> 1. **Severity is human-judged, structurally enforced** (`severity_source: Literal["human"]` field; no auto-classifier produces a severity field). bugbug auto-classifies bugtype; trIAge LLM-prioritizes; RaschidJFR LLM-judges impact + effort. lodestar restores human judgment as the load-bearing PQE artifact.
> 2. **Cross-tool synthesis, not single-repo focus.** Every cited project (bugbug, trIAge, RaschidJFR, all hobby projects) operates on one repo at a time. lodestar synthesizes across multiple agentic-coding tools to surface what matters in the category, not in one product.
> 3. **PQE-shaped weekly external report.** Output is a Markdown priority report consumable in 5 minutes by a PM or engineering leader, not a CSV of scored issues, not in-thread bot responses, not a dashboard. The PQE judgment artifact is the per-item severity reasoning written by hand on top of pipeline-curated candidates.

## Adopted ideas (with attribution in writeup)

| Idea | Source | Adaptation in lodestar |
|---|---|---|
| Ingest → features → analytics → output pipeline pattern | Mozilla bugbug | Pipeline + parquet snapshots between stages; same conceptual shape, different output |
| Weighted engagement-signal traction formula | RaschidJFR/github-issue-analyzer | lodestar ranker uses similar signal mix (comments, commenters, reactions, recency) but explicitly does NOT include LLM-judged impact/effort in the score |
| Issue triage primitives (categorize, dedup, prioritize, link) | trIAge | Apply at corpus level (batch) instead of per-issue (conversational) |
| TF-IDF theme clustering for issue corpora | (general technique, no single source) | Applied as descriptive analytics, not classification |

## Deliberate divergences (with rationale)

| Divergence | Rationale |
|---|---|
| Cross-tool, not single-repo | The PQE-User-Ops role at a developer-tools company synthesizes signal across the category, not just one product's repo |
| Human-judged severity, structurally enforced | JD asks for human judgment on severity; v2 form-check P0 flagged auto-severity as scope creep; structural enforcement (`severity_source` literal type) prevents drift |
| Descriptive analytics over classifiers | Small corpus (1500-3000 issues over 4-week window) doesn't support classifier accuracy claims; descriptive stats (n per tool, dedup rate, theme cluster sizes) are honestly defensible |
| Weekly external Markdown report, not bot/dashboard | Consumer persona (PM/eng-leader, 5-min read on Monday) drives the output shape; Gherkin scenarios verify the read-flow |
| No auto-classification of impact/effort | RaschidJFR's LLM-judged impact/effort would defeat the PQE-judgment demonstration; lodestar keeps these as report-time human rationale fields |

## Gaps remaining in prior art

- **No public artifact** addresses cross-tool VoC synthesis for AI-coding-tools specifically `[verified via no-hits search + low-star single-repo alternatives]`
- **No public artifact** demonstrates the PQE-shape (human-severity + curated top-N + concrete engineering response) as a portfolio demonstration `[inferred, searched for "PQE portfolio" + "quality engineer portfolio github" yielded resume sites, no project artifacts]`
- **Issue-similarity / dedup at scale** has academic treatment but few maintained open-source implementations `[verified via empty MCP search for "duplicate bug detection" + "github issues clustering"]`

lodestar v0 ships into these gaps.

## What this prior-art exercise produced for the architecture plan

- **F2 (bugbug MPL-2.0) confirmed** `[verified]`: derivative work + commercial use permitted with file-level source-share; lodestar doesn't even fork bugbug code, only references the pipeline pattern as inspiration
- **A2-A4 (issue volumes) verified** `[verified via API]`: Aider 13/wk, Cline 38/wk, Continue 93/wk over 90-day window; threshold lowered to 4-week rolling window with no per-tool floor (Wei decision)
- **A7 (GitHub TOS) resolved** `[verified]`: public-content access + Apache-2.0-issue-license inheritance permits redistribution with attribution; conservative path retained (ID + URL + short excerpt) for ethics, not legal necessity
- **F5 (LLM cost) verified** `[verified]`: Haiku 4.5 at $1/$5 per Mtoken → ~$0.55/week for 600 calls/week, well under $5/week budget
- **Ranker formula informed** by RaschidJFR's traction weighting; lodestar's variant cited in writeup

All findings will land in the architecture plan's Pass 4.5 closure section in the next plan edit.
