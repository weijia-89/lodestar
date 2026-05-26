# lodestar

**Status:** v0-min portfolio demonstration. Shipped 2026-05-18; in active extension toward v0.1.
**License:** MIT.
**Scope:** Public Voice-of-Customer (VoC) pipeline for open-source agentic coding tools, exercised end-to-end against Aider in v0-min, with Cline and Continue ingest mappers scaffolded for v0.1. The shape is an AI-assisted VoC plus agentic-bug-prioritization program running entirely on public data.

This is a portfolio demonstration, not a production VoC system and not a statistically powered study. It analyzes the full observed weekly issue population for the target tool, ranks descriptively, and routes a top-N to human review. It does not auto-classify severity (human judgment, by design) and does not claim inferential validity (descriptive analytics only).

---

## What this is

Public agentic coding tools accumulate thousands of GitHub Issues per month. There is no public, reproducible artifact that:

1. Ingests issues across multiple agentic-coding tools into a common schema
2. Deduplicates the resulting corpus (fuzzy + semantic clustering)
3. Surfaces "what matters most" descriptively across the full weekly issue population for each tool (no sampling claim; v0 takes the full available cohort)
4. Lets a human reviewer focus judgment effort on a top-N while the pipeline handles scale
5. Carries a worked customer-escalation handoff through end-to-end in PQE (Product Quality Engineer) shape

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
│   ├── ingest/      Per-tool GitHub Issues ingest (Aider mapper shipped; Cline + Continue scaffolded)
│   ├── dedup/       Fuzzy title + semantic embedding dedup
│   ├── moderate/    Regex PII filter (load-bearing privacy gate)
│   ├── rank/        Engagement * recency * label_weight ranker with calibrate mode
│   ├── report/      Rationale-slot CSV emitter for the human reviewer
│   └── analytics/   Descriptive analytics (NOT auto-severity); TF-IDF themes shipped
├── tests/           172 tests; mutmut at 76% kill rate on dedup + rank + moderate + report
├── docs/
│   ├── PRIOR_ART.md       Mozilla bugbug, trIAge, BugSwarm, ClearFlask, GH SecLab
│   ├── WRITEUP.md         500-word v0-min writeup (entry point for reviewers)
│   ├── ADVERSARIAL_REVIEW_2026-05-18.md   Multi-pass evidence-based code review
│   ├── WORKED_ESCALATION.md  Index to the canonical escalation in reports/
│   └── MANIFEST.md        Wei's personal Cursor manifest (frictions + workflows)
├── reports/
│   ├── aider-week.csv + aider-week.md   Week-1 Aider priority report, rationale filled in
│   └── escalation-aider-5131-benchmark-flag-mismatch.md   Worked escalation, v0-min
├── scripts/
│   ├── repro/aider-5131/   ~10s grep-based repro harness for the escalation
│   ├── form_check_score.py
│   └── run_mutmut.sh
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

- **No auto-severity-classification.** Severity is the PQE-judgment artifact this project keeps in human hands. Auto-classifying it would defeat the point. Pipeline surfaces candidates; human picks and writes rationale.
- **Full-population descriptive ranker.** Candidate-ranker ingests the full observed window of issue population for the target tool, ranks by recency × labels × engagement-signal, surfaces the top-20 to a human reviewer who writes rationale on the top N (top-3 in v0-min, target top-5 by v0.1). No sampling claim; the corpus is the observed cohort.
- **Descriptive analytics over classifiers.** TF-IDF theme clustering, volume/recency/MTTC stats, dedup. No accuracy claims, no IRR overreach.
- **Moderation/PII filter before any report downstream.** Keyword + LLM scan; ethics layer is the JD's "humans need to stay in the loop" principle made structural.
- **Public-data only.** Zero proprietary references; nothing pulled from Intuit, Mailchimp, or Cursor internals.

## Build status (v0-min, 2026-05-18)

| Component | Status |
|---|---|
| Repo scaffold, LICENSE, CI | ✅ Day 1 done |
| Ingest pipeline (Aider mapper) | ✅ |
| Ingest mappers (Cline, Continue) | ✅ code shipped; not exercised in v0-min (Aider only) |
| Dedup layer (fuzzy + semantic + golden fixture) | ✅ |
| Moderation/PII filter | ✅ regex-based; zero mutation survivors on `voc/moderate/patterns.py` |
| Candidate-ranker | ✅ (see `docs/superpowers/specs/2026-05-17-ranker-design.md`) |
| Ranker `--calibrate` mode | ✅ per-component score distribution stats |
| Rationale-slot CSV emitter | ✅ `voc/report/rationale_csv.py` |
| Aider Week-N priority report (template) | ✅ `reports/aider-week.csv` + `reports/aider-week.md` |
| Aider Week-N rationale × 3 (Wei prose) | ✅ `reports/aider-week.md` |
| 500-word writeup | ✅ `docs/WRITEUP.md` |
| Adversarial code review with public fix ledger | ✅ `docs/ADVERSARIAL_REVIEW_2026-05-18.md` |
| Mutation testing (dedup + rank + moderate + report) | ✅ 76% kill rate; `bash scripts/run_mutmut.sh` |
| Form-check pre-score calibration | ✅ via `scripts/form_check_score.py` |
| Descriptive analytics + TF-IDF theme clustering | ✅ `voc/analytics/themes.py` |
| Cross-tool coverage (Cline + Continue priority reports) | 🚧 [v0.1] |
| Multi-week coverage (≥2 weeks per tool) | 🚧 [v0.1] |
| Public-source voice synthesis (Reddit + HN) | 🚧 [v0.1] |
| Worked escalation (aider#5131, grep-based static evidence) | ✅ `reports/escalation-aider-5131-benchmark-flag-mismatch.md` |
| Cursor product-familiarity manifest | ✅ `docs/MANIFEST.md` |
| Demo recording (5 min one-take) | 🚧 [v0.1] |

## v0.1 roadmap

What v0-min ships is one tool (Aider), one week, top-3 rationales, a 500-word writeup, a worked escalation against aider#5131, a Cursor product-familiarity manifest, and TF-IDF theme clustering on the weekly corpus. v0.1 adds:

1. **Cross-tool coverage.** Cline + Continue priority reports against the same pipeline; the ingest mappers already exist.
2. **Multi-week coverage.** Two consecutive weeks per tool so trends become visible.
3. **Voice synthesis pillar.** Reddit (r/ChatGPTCoding) + Hacker News public-thread synthesis, with the same PII regex applied as the GitHub Issues path. Output: one synthesis memo per tool per week, cross-referenced with the priority report.
4. **5-minute demo recording.** Single take, walking through the priority report + writeup + escalation.

Each v0.1 pillar has a Wei time estimate and a deferrable-vs-not tag. The honest framing is, v0-min is the shape of the demonstration and v0.1 is the demonstration at portfolio scale.

## Quick start

```bash
git clone https://github.com/weijia-89/lodestar
cd lodestar
pip install -e ".[dev]"
pytest

# v0-min: pull last 90 days from Aider (extend to cline / continue in v0.1):
python -m voc.ingest --tool aider --window 90 --output data/aider-90d.parquet

# Dedup the corpus:
python -m voc.dedup --input data/aider-90d.parquet --output data/aider-dedup.parquet

# Flag PII before ranking (regex-only; reviewer decides disposition):
python -m voc.moderate --input data/aider-dedup.parquet --output data/aider-moderated.parquet

# Inspect the score distribution before picking a top-N cutoff:
python -m voc.rank --input data/aider-moderated.parquet --calibrate

# Rank top-20 candidates for the week:
python -m voc.rank --input data/aider-moderated.parquet --output data/aider-ranked.parquet --top 20

# Emit a rationale-slot CSV for the human reviewer to fill in (top-3 in v0-min):
python -m voc.report.rationale_csv --input data/aider-ranked.parquet --output reports/aider-week.csv --top 3
```

### Optional: Playwright escalation harness (T25)

Browser-based bug reproduction lives under `tests/escalation/`. These tests are
opt-in: each module skips collection when Playwright is not installed
(`importorskip`), so CI and default `pytest` without `[escalation]` never load
them. Tests are auto-tagged with the `escalation` marker; filter explicitly
with `-m "not escalation"` or `-m escalation` when needed.

```bash
pip install -e ".[escalation]"
playwright install chromium
pytest tests/escalation/test_playwright_smoke.py -x
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

This is a portfolio demonstration project. If you're a hiring manager evaluating it, the 500-word writeup at `docs/WRITEUP.md` is the intended entry point, followed by `reports/aider-week.md` for the priority report Wei wrote rationale on, then `reports/escalation-aider-5131-benchmark-flag-mismatch.md` for the worked escalation, and `docs/ADVERSARIAL_REVIEW_2026-05-18.md` for the review discipline.
