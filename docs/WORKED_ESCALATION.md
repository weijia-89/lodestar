# Worked escalation, index

The canonical worked escalation for v0-min lives in `reports/`. This file used to be a Playwright-shaped template; the actual escalation I shipped is grep-shaped (static evidence against a pinned upstream SHA) because the bug I picked is a flag-name mismatch between code and docs, not a UI rendering bug.

## Canonical artifact

[`reports/escalation-aider-5131-benchmark-flag-mismatch.md`](../reports/escalation-aider-5131-benchmark-flag-mismatch.md), targeting [Aider issue #5131](https://github.com/Aider-AI/aider/issues/5131). My P2 severity call, defended in both directions, with a recommended one-line fix that preserves backward compatibility.

## Reproduction

[`scripts/repro/aider-5131/repro.sh`](../scripts/repro/aider-5131/repro.sh) clones aider at the pinned main SHA, runs four grep probes against the source, and PASS/FAIL declares whether each probe finds the evidence the report names. Runs in ~10 seconds, no API key required, $0 cost.

```bash
bash scripts/repro/aider-5131/repro.sh
```

## Why grep, not Playwright

The bug at issue #5131 is `benchmark/benchmark.py` rejecting the `--model-settings-file` flag that the aider docs document as the canonical name for the same capability. The evidence is two source-line locations and a docs-link bridge between them. Static evidence is the right tool; a Playwright trace would not surface more information than the four grep probes already do. When the next escalation involves a UI surface (a Cursor IDE rendering bug, a Cline web extension bug), the Playwright harness in `tests/escalation/` is wired up and ready.

## Future shape

When v0.1 lands a second escalation, this file becomes a real index over multiple worked artifacts. Until then, the link above is the artifact.
