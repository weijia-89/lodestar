# lodestar - agent operating guide

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
  schema-breaking changes, irreversible production writes (none of these
  currently apply to lodestar v0)

## Review gates (require Wei approval)

- Adding any new optional-dependency group to `pyproject.toml`
- Changing `voc/dedup/tfidf.py:TFIDF_CONFIG` (impacts golden test baselines)
- Changing fuzzy / semantic thresholds in `voc/dedup/__main__.py`
- Editing prose in `docs/WRITEUP.md`, `docs/MANIFEST.md`
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

## Mutation testing (mutmut, dedup + rank + moderate + report layers)

Mutmut is configured under `[tool.mutmut]` in `pyproject.toml`. Runs against
`voc/dedup/`, `voc/rank/`, `voc/moderate/`, and `voc/report/` with the
corresponding test suites as the kill source.

```
bash scripts/run_mutmut.sh           # foreground (~3 min wall clock)
bash scripts/run_mutmut.sh --detach  # background, prints PID + log path
python -m mutmut results             # show survivors
python -m mutmut show <mutant_name>  # see the diff for one mutant
```

Last run (2026-05-18, post-moderate+report addition to paths_to_mutate):

- **76.0% kill rate** (240 of 316 covered mutants killed, 75 survived, 1 timeout)
- ~316 covered mutants + 121 rank.__main__ "no tests" mutants + 78 dedup.__main__
  + 57 report + 40 moderate "no tests" mutants (argparse/CLI code, by design)
- Kill rate dropped from 86.1% (dedup+rank only) to 76.0% because the newly
  covered moderate + report modules contribute 23 equivalent-mutant survivors

Survivor distribution by module:

| Module | Survivors | Class |
|---|---|---|
| voc.rank.__main__ | 22 | pandas pass-through, equivalent index=False/None |
| voc.report.rationale_csv | 12 | csv writer pass-through, equivalent header order |
| voc.moderate.__main__ | 11 | equivalent empty-df dtype handling; argparse defaults |
| voc.dedup.__main__ | 11 | argparse + CLI; equivalent default-arg mutations |
| voc.dedup.semantic | 7 | inner-loop range symmetric; equivalent threshold tweaks |
| voc.rank.ranker | 5 | top_n config-passthrough; equivalent upstream defaulting |
| voc.dedup.fuzzy | 5 | range/symmetric union-find equivalents |
| voc.rank.signals | 2 | `<=0` vs `<0` boundaries where math collapses to same value |

**Load-bearing privacy code has zero survivors:** `voc.moderate.patterns`
(the regex PII detector, the actual privacy gate per the AGENTS.md
refusal list) does NOT appear in the survivor list. Every mutant against
the regex patterns was killed by the test suite. That is the right
place to be strict; argparse equivalents are not.

Remaining survivors are dominated by equivalent mutants where the code
under mutation produces the same observable behavior through different
paths (e.g. `pd.Series(dtype="object")` vs `None` for an empty
pii_flags column). Killing those would require pedantic dtype assertions
that exceed the actual spec.

The `tests/dedup/conftest.py` includes a `multiprocessing.set_start_method`
monkey-patch needed for mutmut+Python 3.14 compatibility. Harmless under
normal pytest runs.

The `tests/rank/test_cli.py` subprocess-CLI test uses a `_UNDER_MUTMUT`
gate (cwd-name detection) to skip itself when running inside mutmut's
sandbox, because the trampolined module's import fails when `mutmut.config`
is None in the subprocess.

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

## Known limits (honest acknowledgment, v0.1)

The portfolio narrative is "AI-assisted with full review discipline." That
discipline has known gaps documented here so reviewers see them in advance
rather than discovering them as surprises:

- **mypy is enforced (v0.2 fitness function lifted 2026-05-18).** CI runs
  `mypy voc/` and fails the build on type errors. `pandas-stubs` and
  `scipy-stubs` are pinned in the dev group (see `pyproject.toml`). Two
  sklearn imports carry `# type: ignore[import-untyped]  # TODO(v0.2)`
  pending an upstream `py.typed` marker; tracked at `voc/dedup/tfidf.py:10`
  and `voc/dedup/semantic.py:12`. Drop the suppressions when sklearn
  ships the marker.
- **CI Python matrix trails dev.** CI tests on Python 3.11 and 3.12
  (`.github/workflows/ci.yml:15`). Dev runs Python 3.14.5 (see Verified
  library versions above). Once GitHub Actions provides stable 3.14
  runners, add 3.14 to the matrix. Until then, the dev environment is
  ahead of CI.
- **No subprocess-CLI smoke tests for voc.escalation.** The Playwright
  escalation harness is template-only at v0; the real reproduction is
  written by Wei when an actual bug is selected. The smoke test in
  `tests/escalation/test_playwright_smoke.py` uses example.com to verify
  the harness wires up correctly.

## CLI flag convention (locked in 2026-05-18)

Every CLI module in `voc.*` accepts `--input` and `--output` as the
canonical flags. The legacy `--in` / `--out` short forms (originally on
`voc.dedup` and `voc.ingest`) remain as backward-compat aliases. New CLIs
must use `--input` / `--output` only.

Subprocess CLI smoke tests live in `tests/<module>/test_cli_smoke.py` and
are required for every module that exposes a `python -m voc.<module>`
entry point. The rank module's tests caught real bugs; the dedup/ingest
tests were added 2026-05-18 to backfill the same coverage after an
adversarial review surfaced a README-vs-CLI divergence.

## Iron-law incidents (this repo's contribution to the safe-terminal log)

Logged in calibration.jsonl entries. Recurring pattern: multi-line
`python3 -c` strings for sklearn/rapidfuzz exploration. Mitigation: write
to `/tmp/lodestar_<task>_probe.py` and invoke as a single-line command.

## Cursor Cloud specific instructions

The update script runs `uv pip install -e ".[dev]"` inside a venv at
`/agent/repos/lodestar/.venv`. Activate with `source .venv/bin/activate`
before running `pytest`, `mypy voc/`, or `ruff check voc/ tests/`.

- **Tests:** `pytest --timeout=30` (172 passed, 2 skipped on baseline)
- **Lint:** `ruff check voc/ tests/`
- **Type check:** `mypy voc/`
- **Pipeline demo:** `python -m voc.dedup --input tests/fixtures/aider_smoke_66.parquet --output /tmp/out.parquet` then `voc.moderate` then `voc.rank` (same `--input`/`--output` pattern)
- The `voc.report` module has no `__main__.py`; use `voc.report.rationale_csv` as a library.
- `storage.googleapis.com` is blocked by egress restrictions, which prevents Flutter SDK setup for the `buds` repo in the same workspace.
