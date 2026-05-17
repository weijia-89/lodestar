# agentic-voc-bench

**Status:** v0 scaffold — in active build (2026-05-17 onward).
**License:** MIT.
**Scope:** Public, reproducible Voice-of-Customer (VoC) pipeline for open-source agentic coding tools (Aider, Cline, Continue). Demonstrates what an AI-native first-of-its-kind VoC + agentic-bug-prioritization program could look like at its v0, on public data.

This is a v0 demonstration project, not a production VoC system. It deliberately does NOT auto-classify severity — that is a human-judgment artifact in this project, per the design rationale below.

---

## What this is

Public agentic coding tools accumulate thousands of GitHub Issues per month. There is no public, reproducible artifact that:

1. Ingests issues across multiple agentic-coding tools into a common schema
2. Deduplicates the resulting corpus (fuzzy + semantic clustering)
3. Surfaces "what matters most" with statistically defensible sampling (n≥200 issues/tool/week)
4. Lets a human reviewer focus judgment effort on a curated top-N while the pipeline handles scale
5. Demonstrates a worked customer-escalation handoff in PQE (Product Quality Engineer) shape

`agentic-voc-bench` is a v0 of that artifact.

## What this is not

- Not a production VoC tool
- Not a model-eval benchmark
- Not an auto-severity-classifier (severity is human judgment in this project)
- Not a customer support intake tool (ClearFlask is the customer-facing twin)
- Not a generic LLM-eval pipeline

## Repository layout (v0 scaffold)

```
agentic-voc-bench/
├── voc/
│   ├── ingest/      Per-tool GitHub Issues ingest (Aider, Cline, Continue)
│   ├── dedup/       Fuzzy title + semantic embedding dedup
│   ├── classify/    Descriptive analytics (NOT auto-severity); TF-IDF clusters
│   └── report/      Weekly priority report generator
├── tests/
├── interviews/      Customer interview transcripts (gitignored; consent-gated)
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

**Gap statement:** No public artifact addresses cross-repo Voice-of-Customer synthesis for AI-coding tools specifically. `agentic-voc-bench` v0 fills that gap.

## Design choices (with rationale)

- **No auto-severity-classification.** Severity is the PQE-judgment artifact this project demonstrates. Auto-classifying it would defeat the demonstration. Pipeline surfaces candidates; human picks and writes rationale.
- **Statistical defensibility on the source pool.** Candidate-ranker pulls n≥200 issues/tool/week sampled across recency × labels × engagement-signal; human reviews curated top-20, writes rationale on top 5.
- **Descriptive analytics over classifiers.** TF-IDF theme clustering, volume/recency/MTTC stats, dedup. No accuracy claims, no IRR overreach.
- **Moderation/PII filter before any report downstream.** Keyword + LLM scan; ethics layer is the JD's "humans need to stay in the loop" principle made structural.
- **Public-data only.** Zero proprietary references. No Intuit, Mailchimp, or Cursor-internal information.

## Build status (as of 2026-05-17)

| Component | Status |
|---|---|
| Repo scaffold, LICENSE, CI | ✅ Day 1 done |
| Ingest pipeline (Aider/Cline/Continue) | 🚧 next |
| Dedup layer | 🚧 |
| Moderation/PII filter | 🚧 |
| Candidate-ranker | 🚧 |
| Descriptive analytics + TF-IDF | 🚧 |
| Customer interviews | 🚧 |
| Priority reports × 2 weeks | 🚧 |
| Worked escalation (Playwright) | 🚧 |
| Cursor product-familiarity manifest | 🚧 |
| Writeup (2000 words) | 🚧 |
| Demo recording (5 min) | 🚧 |

## Quick start (when ingest lands)

```bash
git clone https://github.com/wjia-2/agentic-voc-bench
cd agentic-voc-bench
pip install -e ".[dev]"
pytest
# Pull last 90 days from each tool:
python -m voc.ingest --tool aider --days 90
python -m voc.ingest --tool cline --days 90
python -m voc.ingest --tool continue --days 90
```

## Author

Wei Jia. Built solo, AI-assisted, public, 2026-05.

This is a portfolio demonstration project. If you're a hiring manager evaluating it, the writeup at `docs/WRITEUP.md` (when it lands) is the intended entry point.
