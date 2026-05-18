# lodestar

**Status:** v0 portfolio demonstration. In active build (2026-05-17 onward).
**License:** MIT.
**Scope:** Public Voice-of-Customer (VoC) pipeline for open-source agentic coding tools (Aider, Cline, Continue). Demonstrates the shape of an AI-native first-of-its-kind VoC + agentic-bug-prioritization program on public data.

This is a portfolio demonstration, not a production VoC system and not a statistically powered study. It analyzes the full observed weekly issue population for each tool, surfaces themes descriptively, and routes a curated top-N to human review. It does not auto-classify severity (human judgment, by design) and does not claim inferential validity (descriptive analytics only).

---

## What this is

Public agentic coding tools accumulate thousands of GitHub Issues per month. There is no public, reproducible artifact that:

1. Ingests issues across multiple agentic-coding tools into a common schema
2. Deduplicates the resulting corpus (fuzzy + semantic clustering)
3. Surfaces "what matters most" descriptively across the full weekly issue population for each tool (no sampling claim; v0 takes the full available cohort)
4. Lets a human reviewer focus judgment effort on a curated top-N while the pipeline handles scale
5. Demonstrates a worked customer-escalation handoff in PQE (Product Quality Engineer) shape

`lodestar` is a v0 of that artifact.

## What this is not

- Not a production VoC tool
- Not a statistically powered study (no sampling claim, no significance testing, no IRR overreach)
- Not a model-eval benchmark
- Not an auto-severity-classifier (severity is human judgment in this project)
- Not a customer support intake tool (ClearFlask is the customer-facing twin)
- Not a generic LLM-eval pipeline

## Repository layout (v0 scaffold)

```
lodestar/
├── voc/
│   ├── ingest/      Per-tool GitHub Issues ingest (Aider, Cline, Continue)
│   ├── dedup/       Fuzzy title + semantic embedding dedup
│   ├── classify/    Descriptive analytics (NOT auto-severity); TF-IDF clusters
│   ├── synthesis/   Public-source voice synthesis memos (per tool / per week)
│   └── report/      Weekly priority report generator
├── tests/
├── docs/
│   ├── PRIOR_ART.md     Mozilla bugbug, trIAge, BugSwarm, ClearFlask, GH SecLab
│   ├── METHODOLOGY.md   Sampling design, dedup approach, moderation/PII filter
│   ├── WORKED_ESCALATION.md  Playwright-based bug reproduction example
│   └── MANIFEST.md      Cursor product-familiarity manifest (private notes)
├── reports/         Weekly priority reports (hand-written, with Cascade scaffolding)
├── pyproject.toml
├── LICENSE
└── README.md
```

## Prior art (full treatment in `docs/PRIOR_ART.md`)

| Project | License | What it does | Where we diverge |
|---|---|---|---|
| Mozilla `bugbug` | MPL-2.0 | ML bug classification on Bugzilla/Firefox | Cross-repo GitHub instead of one Bugzilla; no auto-severity |
| `trIAge` (latentspace-lab) | TBD | LLM-driven per-repo issue/PR analyzer | Cross-repo synthesis instead of per-repo |
| GitHub Security Lab `taskflow-agent` | unknown | LLM triage for CodeQL alerts | Pattern reference for prompt design |
| BugSwarm | academic | CI-failure artifacts benchmark | User-VoC for AI tools (different problem) |
| ClearFlask | open-source | Customer-facing feedback intake | Internal-analytics complement, not customer-facing |

**Gap statement:** No public artifact addresses cross-repo Voice-of-Customer synthesis for AI-coding tools specifically. `lodestar` v0 fills that gap.

## Design choices (with rationale)

- **No auto-severity-classification.** Severity is the PQE-judgment artifact this project demonstrates. Auto-classifying it would defeat the demonstration. Pipeline surfaces candidates; human picks and writes rationale.
- **Full-population descriptive ranker.** Candidate-ranker ingests the full observed weekly issue population for each tool (Aider, Cline, Continue), ranks by recency × labels × engagement-signal, surfaces a curated top-20 to a human reviewer who writes rationale on top 5. No sampling claim; the v0 corpus is the observed cohort.
- **Descriptive analytics over classifiers.** TF-IDF theme clustering, volume/recency/MTTC stats, dedup. No accuracy claims, no IRR overreach.
- **Moderation/PII filter before any report downstream.** Keyword + LLM scan; ethics layer is the JD's "humans need to stay in the loop" principle made structural.
- **Public-data only.** Zero proprietary references. No Intuit, Mailchimp, or Cursor-internal information.

## Build status (as of 2026-05-17)

| Component | Status |
|---|---|
| Repo scaffold, LICENSE, CI | ✅ Day 1 done |
| Ingest pipeline (Aider/Cline/Continue) | ✅ |
| Dedup layer (fuzzy + semantic + golden fixture) | ✅ 84.8% mutation kill rate |
| Moderation/PII filter | ✅ regex-based; `voc/moderate/` |
| Candidate-ranker | ✅ (see `docs/superpowers/specs/2026-05-17-ranker-design.md`) |
| Ranker `--calibrate` mode | ✅ per-component score distribution stats |
| Rationale-slot CSV emitter | ✅ `voc/report/rationale_csv.py` |
| Descriptive analytics + TF-IDF | 🚧 |
| Public-source voice synthesis × 2 weeks (no live interviews, v0 is public-data-only) | 🚧 |
| Priority reports × 2 weeks | 🚧 |
| Worked escalation (Playwright) | ✅ scaffold |
| Cursor product-familiarity manifest | ✅ skeleton (prose-fill by author) |
| Writeup (2000 words) | ✅ skeleton (prose-fill by author) |
| Demo recording (5 min) | ✅ script skeleton (recording by author) |
| Mutation testing on dedup + rank | ✅ via mutmut; `bash scripts/run_mutmut.sh` |
| Form-check pre-score calibration | ✅ via `scripts/form_check_score.py` |

## Quick start

```bash
git clone https://github.com/wjia-2/lodestar
cd lodestar
pip install -e ".[dev]"
pytest

# Pull last 90 days from each tool (writes to data/<tool>-*.parquet):
python -m voc.ingest --tool aider --days 90
python -m voc.ingest --tool cline --days 90
python -m voc.ingest --tool continue --days 90

# Dedup the corpus:
python -m voc.dedup --input data/aider-90d.parquet --output data/aider-dedup.parquet

# Flag PII before ranking (regex-only; reviewer decides disposition):
python -m voc.moderate --input data/aider-dedup.parquet --output data/aider-moderated.parquet

# Inspect the score distribution before picking a top-N cutoff:
python -m voc.rank --input data/aider-moderated.parquet --calibrate

# Rank top-20 candidates for the week:
python -m voc.rank --input data/aider-moderated.parquet --output data/aider-ranked.parquet --top 20

# Emit a rationale-slot CSV for the human reviewer to fill in:
python -m voc.report.rationale_csv --input data/aider-ranked.parquet --output reports/aider-week.csv --top 5
```

The ranker output adds `recency_score`, `engagement_score`, `label_score`,
`composite_score`, and `rank` columns. The composite is a candidate-priority
signal for human review, NOT a severity classification.

The moderation stage adds a `pii_flags` column listing detected PII
categories (email, phone, ssn, credit_card). Rows are never redacted or
dropped; the reviewer decides disposition.

The rationale CSV has four empty columns for the human reviewer:
`rationale`, `severity_assessment`, `action_needed`, `reviewer`. Severity
is a column the human fills in, by project design.

## Author

Wei Jia. Built solo, AI-assisted, public, 2026-05.

This is a portfolio demonstration project. If you're a hiring manager evaluating it, the writeup at `docs/WRITEUP.md` (when it lands) is the intended entry point.
