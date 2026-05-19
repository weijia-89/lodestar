# Changelog

All notable changes to lodestar live here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/). The project
runs on a v0-min → v0.1 → ... portfolio-iteration cadence rather than
production semver.

## [Unreleased]

Planned for v0.1:

- Cross-tool coverage: Cline + Continue priority reports against the same
  pipeline (ingest mappers already exist).
- Multi-week coverage: at least two consecutive weeks per tool, so trends
  become visible.
- Public-source voice synthesis: Reddit (r/ChatGPTCoding) + Hacker News
  public-thread synthesis, with the same PII regex applied as the GitHub
  Issues path.
- 5-minute demo recording. Single take, narrated through the priority
  report and out into the worked escalation.

## [v0-min-polish] - 2026-05-19

Same-night polish after the v0-min ship, mostly about closing the gap
between what shipped and how the repo described it.

### Added

- CHANGELOG.md (this file).
- README repository-layout block now surfaces
  `reports/escalation-aider-5131-benchmark-flag-mismatch.md` and
  `scripts/repro/aider-5131/` as first-class artifacts.

### Changed

- WRITEUP.md private-telemetry section rewritten around two
  forum-grounded clusters: a destructive-action incident index citing
  threads 129401 and 152325 plus the 2025 Replit production-database
  deletion, and the PLAN-mode violation cluster across threads 151802,
  147589, and 148247 (unacknowledged by Cursor staff at writing time)
  with proactive-gating as the proposed fix direction. Previous draft
  was AI-shaped at the framing level.
- WRITEUP.md "Honest limitations" rewritten in scoping voice: one tool,
  a little more than a single day, lone reviewer, rationales as the
  human-in-the-loop review.
- README build-status table caught up with reality: four rows flipped
  from 🚧 to ✅ (Aider Week-N rationale × 3, TF-IDF theme clustering,
  worked escalation against aider#5131, Cursor product-familiarity
  manifest). The items had shipped earlier; the table hadn't.
- README v0.1 roadmap purged of three completed items (TF-IDF themes,
  worked escalation, Cursor manifest); the remaining four pillars are
  the genuine v0.1 work.
- docs/MANIFEST.md placeholder replaced with the falsifiable-hypotheses
  -index methodology and the Cursor 800-reports-per-month framing.
- docs/WORKED_ESCALATION.md collapsed from Playwright-shaped template
  into a short index pointing at the shipped grep-based aider#5131
  artifact under reports/.

### Removed

- docs/DEMO_SCRIPT.md and tests/writeup/test_demo_script.py. v0-min
  ships without a demo script; WRITEUP.md is the demo.
- tests/escalation/test_handoff_template.py. The handoff template no
  longer exists after the worked-escalation rewrite.

### Fixed

- README repo-layout reference to `voc/classify/` corrected to
  `voc/analytics/themes.py`, where the TF-IDF code actually lives.
- tests/writeup/test_writeup_skeleton.py honest-framing assertion
  broadened to recognize the actual "observation of the full open-issue
  population" phrasing in Methodology. I widened only the literal-string
  match; the semantic contract is preserved.

## [v0-min] - 2026-05-18

Initial portfolio ship. Public Voice-of-Customer pipeline for
open-source agentic coding tools, exercised end-to-end against Aider.

### Pipeline

- `voc.ingest`: GitHub Issues HTTP client with pagination and 429/5xx
  retry; per-tool mappers for Aider, Cline, and Continue (Aider only
  exercised in v0-min); SHA-256 author hashing; parquet round-trip;
  idempotent CLI with `--force` and mtime-based <1h skip.
- `voc.dedup`: fuzzy title clustering + semantic embedding pass +
  union-find merge; golden regression fixture on a live Aider corpus.
- `voc.moderate`: regex-based PII flag pipeline; zero mutation
  survivors on `voc/moderate/patterns.py`.
- `voc.rank`: engagement × recency × label-weight candidate ranker
  with a `--calibrate` flag that prints per-component score
  distribution stats before picking a top-N cutoff.
- `voc.report.rationale_csv`: rationale-slot CSV emitter with four
  empty columns for the human reviewer (rationale, severity_assessment,
  action_needed, reviewer).
- `voc.analytics.themes`: TF-IDF + MiniBatchKMeans descriptive theme
  clustering with `random_state=0`; graceful degrade on empty,
  single-issue, or vocabulary-collapse inputs.

### Reports

- `reports/aider-week.csv` and `reports/aider-week.md`: Week-1 Aider
  priority report with three rationales filled in by hand on the top
  candidates.
- `reports/escalation-aider-5131-benchmark-flag-mismatch.md`: worked
  customer-escalation handoff against [Aider issue #5131](https://github.com/Aider-AI/aider/issues/5131),
  P2 severity defended in both directions with a one-line recommended
  fix that preserves backward compatibility.
- `scripts/repro/aider-5131/repro.sh`: ~10-second four-probe repro
  harness running grep against the pinned upstream SHA. No API key, $0
  cost.

### Docs

- `docs/WRITEUP.md`: 500-word v0-min writeup for hiring-manager review.
- `docs/MANIFEST.md`: Cursor product-familiarity manifest sourced from
  public observation.
- `docs/PRIOR_ART.md`: comparison against Mozilla bugbug, trIAge,
  BugSwarm, ClearFlask, and GitHub SecLab taskflow-agent.
- `docs/ADVERSARIAL_REVIEW_2026-05-18.md`: multi-pass evidence-based
  code review with a public fix ledger.

### Testing + tooling

- 172 tests across the pipeline; mutmut at 76% kill rate on dedup +
  rank + moderate + report.
- mypy enforced on `voc/` in CI; pandas-stubs and scipy-stubs added to
  the dev group.
- Form-check pre-score calibration via `scripts/form_check_score.py`.

### Design choices

- No auto-severity classification: severity is the PQE-judgment artifact
  the project keeps in human hands.
- Full-population descriptive ranker: no sampling claim; the corpus is
  the observed cohort.
- Descriptive analytics over classifiers: no accuracy claims, no IRR
  overreach.
- Public-data only: zero proprietary references; nothing pulled from
  Intuit, Mailchimp, or Cursor internals.
