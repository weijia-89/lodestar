# lodestar — agent operating guide

Symlinked / mirrored as `AGENTS.md`. Public-source VoC v0 demonstration for
agentic coding tools. This file scopes what agents do in this repo and what
gates apply.

## What this repo is

A reproducible Voice-of-Customer pipeline that ingests GitHub issues for
Aider / Cline / Continue, deduplicates them, ranks by engagement-recency-label,
and produces a top-20 priority report with human-written rationale for the
priority five. Voice synthesis pulls public discussion from Reddit and HN.
Pillars are Tier-1 PQE-judgment artifacts (priority reports, voice synthesis
memos, worked escalation, Cursor manifest, demo recording). The pipeline is
supporting infrastructure, not the demonstration itself.

## What it isn't (refusal list)

The agent will NOT (without a documented forcing-constraint ADR):

- Add microservices, Kubernetes, event bus, CQRS, or "scalable" architecture
- Add LLM-based moderation as the load-bearing privacy gate (PII regex is
  load-bearing; LLM augmentation is bypassable)
- Add severity auto-classification (severity is human judgment by design)
- Claim statistical inference (descriptive only; no sampling, no significance)
- Add customer-interview pillar (Wei has no public-recruit network for
  Aider/Cline/Continue communities; IP-locked at Intuit)
- Use banned vibe-coding vocab (`leverage`, `utilize`, `robust solution`,
  `comprehensive analysis`) without naming the concrete property

## Vibe-safety tiers

Per form-check Section 5 (operator-uncalibrated; treat as procedural
defaults, not data-driven thresholds, until N≥50 in calibration.jsonl):

- **vibe-safe** (≥80): UI/copy tweaks, scaffolding, internal helpers, log changes
- **vibe-careful** (≥90, with Test ≥80, Hallucination ≥85, Adversarial ≥70):
  dedup config changes, ranker weights, public API additions, schema-additive
  parquet changes, prompt changes
- **vibe-dangerous** (≥95, with Test ≥90, Hallucination ≥90, Adversarial ≥85,
  Reversibility ≥90): anything that would touch auth, payments, secrets,
  schema-breaking changes, irreversible production writes — none of these
  currently apply to lodestar v0

## Review gates (require Wei approval)

- Adding any new optional-dependency group to `pyproject.toml`
- Changing `voc/dedup/tfidf.py:TFIDF_CONFIG` (impacts golden test baselines)
- Changing fuzzy / semantic thresholds in `voc/dedup/__main__.py`
- Editing prose in `docs/WRITEUP.md`, `docs/MANIFEST.md`, `docs/DEMO_SCRIPT.md`
  (these are Wei's voice; agent edits the SKELETON, not the prose)
- Editing the calibration log (`career-help/applications/.recovery/calibration.jsonl`)
  outside of `scripts/form_check_score.py` invocations

## Test-as-spec discipline (TDD red-green-verify)

For every behavior change:

1. Write a failing test (the spec) and run it; record the failure message
2. Implement the minimum to pass
3. Verify the test now passes AND the full suite stays green
4. Verify the green by running pytest, not by claiming it

Tests live alongside source by module: `tests/dedup/`, `tests/ingest/`,
`tests/moderate/`, `tests/rank/`, `tests/escalation/`, `tests/writeup/`,
`tests/ci/`, `tests/scripts/`. The `tests/dedup/conftest.py` `make_issue`
fixture is the single Issue factory for dedup tests.

## Verified library versions (rev when golden test re-baselines)

Recorded 2026-05-17 against `tests/fixtures/aider_smoke_66.parquet`:

```
rapidfuzz 3.14.5, scikit-learn 1.8.0, pyarrow 24.0.0, Python 3.14.5
```

If the Aider-66 golden tests drift (`tests/dedup/test_golden_aider_smoke.py`),
suspect rapidfuzz or sklearn point-release changes before assuming dedup
regression.

## Hallucination check (form-check S3 / hallucination_check)

Before adding any new import, the agent verifies the package on PyPI:
publisher, first-published date (≥30 days), version count, and whether
the requested API exists in the version pinned in `pyproject.toml`.
This is non-negotiable per the SLOP-arXiv hallucinated-package threat
class (Spracklen et al., USENIX 2025: 5.2% commercial / 21.7% OSS-model
hallucination rate).

## Supply-chain hygiene

- All deps in `pyproject.toml` have upper-bound version caps (audited 2026-05-17)
- `pip-audit --strict` runs in CI on every PR (`.github/workflows/ci.yml`)
- Optional `escalation` deps (Playwright + pytest-playwright) are opt-in;
  the default `pip install -e ".[dev]"` does not pull them.

## Iron-law incidents (this repo's contribution to the safe-terminal log)

Logged in calibration.jsonl entries. Recurring pattern: multi-line
`python3 -c` strings for sklearn/rapidfuzz exploration. Mitigation: write
to `/tmp/lodestar_<task>_probe.py` and invoke as a single-line command.
