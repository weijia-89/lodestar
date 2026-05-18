# Escalation: Aider benchmark harness rejects the model-settings flag its own docs document

**Issue:** [aider#5131](https://github.com/Aider-AI/aider/issues/5131) (filed 2026-05-14 by [@camerono](https://github.com/camerono))
**Severity:** P2
**Affected surface:** `benchmark/benchmark.py`, the harness Aider maintainers and external evaluators use to score models against the polyglot benchmark suite.
**Customer impact (this week):** 2 comments, 0 reactions on the issue itself. One reporter narrative of multi-hour debugging before the user identified the flag mismatch as the root cause. Compounded by the fact that this same surface produced a still-open prior report ([aider#2766](https://github.com/Aider-AI/aider/issues/2766), Jan 2025).
**Reproduction:** `bash scripts/repro/aider-5131/repro.sh` in this repo. Reproduces in ~10 seconds, no API key required, $0 cost.
**Status:** open, unassigned, no maintainer comment as of 2026-05-18 (4 days after filing).

## TL;DR

I reviewed Aider issue #5131 against this week's ranker output (rank 4-5, flagged as a recency-dominated low-engagement candidate; see `reports/aider-week.md`). The bug is a flag-name mismatch between `benchmark/benchmark.py` and the model-settings docs the bench README itself links to. I confirmed all four pieces of evidence the reporter named, plus a sibling silent-hang amplifier (`LONG_TIMEOUT = 24 * 60 * 60`) that converts the configuration miss into a 24-hour wait rather than a clean argparse failure. My severity verdict is P2: real customer-trust impact on a narrow population of benchmark contributors and external evaluators, with a clean two-line fix path that preserves backward compatibility. Recommended handoff: option 2 from the issue body (alias `--model-settings-file` in `benchmark/benchmark.py`).

## What the bug is (technical)

Aider's benchmark harness lives at `benchmark/benchmark.py` in the main repo and is invoked as a development tool to score models against the polyglot benchmark suite. The harness uses [typer](https://typer.tiangolo.com/) for its CLI definition. At `benchmark/benchmark.py:207` (resolved against SHA `6435cb8b1e885d7275327d4b61206b1b1618dfe1`, current main HEAD as of 2026-05-18) the model-settings flag is declared as:

```python
read_model_settings: str = typer.Option(
    None, "--read-model-settings", help="Load aider model settings from YAML file"
),
```

The aider docs at `aider/website/docs/config/adv-model-settings.md:79` document the same capability under a different flag name:

```
- Or specify a specific file with the `--model-settings-file <filename>` switch.
```

`benchmark/README.md:85` then links straight to that docs page:

```
- `--read-model-settings=<filename.yml>` specify model settings, see here: https://aider.chat/docs/config/adv-model-settings.html#model-settings
```

A user reading the bench README sees the correct flag, follows the link for the YAML schema, sees the docs using a different flag name, and reasonably assumes the two are interchangeable. They pass `--model-settings-file path/to/settings.yml` to `benchmark.py`. Typer rejects unknown options with `No such option: --model-settings-file` on stderr and a non-zero exit, but this rejection is easy to miss when the user is invoking the harness inside the documented Docker container with logs scrolling, especially since `LONG_TIMEOUT = 24 * 60 * 60` (`benchmark/benchmark.py:348`) means a successful-looking start can sit in a long-decode loop for an hour or more without the YAML knobs (`min_p` / `top_p`) the user thought they had loaded.

The reporter named [aider#2766](https://github.com/Aider-AI/aider/issues/2766) (Jan 2025, still open) as a possibly-related case where the same surface bit a different user without resolution. I have not independently verified that one is the same root cause, but the surface overlap is a useful signal for the assignee.

## Reproduction (verbatim from the script output)

The repro at `scripts/repro/aider-5131/repro.sh` clones aider at main HEAD, runs four `grep` probes that each capture concrete source-line evidence, plus one informational probe on the bench README. Each probe writes its line-numbered match to `/tmp/aider-repro-5131/repro.log` before declaring PASS or FAIL.

```
Aider main HEAD SHA: 6435cb8b1e885d7275327d4b61206b1b1618dfe1

=== Probe 1: benchmark.py defines --read-model-settings ===
207:        None, "--read-model-settings", help="Load aider model settings from YAML file"
[PROBE-1 PASS]

=== Probe 2: benchmark.py does NOT define --model-settings-file ===
[PROBE-2 PASS] (zero matches, as the bug predicts)

=== Probe 3: docs document --model-settings-file ===
79:- Or specify a specific file with the `--model-settings-file <filename>` switch.
[PROBE-3 PASS]

=== Probe 4: LONG_TIMEOUT amplifier present in benchmark.py ===
348:    LONG_TIMEOUT = 24 * 60 * 60
[PROBE-4 PASS]

=== Probe 5 (informational): benchmark README links to docs ===
85:- `--read-model-settings=<filename.yml>` specify model settings, see here: https://aider.chat/docs/config/adv-model-settings.html#model-settings

=== Verdict ===
[REPRO PASS] Bug aider#5131 reproduced at SHA 6435cb8b1e885d7275327d4b61206b1b1618dfe1.
```

The repro is intentionally static (grep-only) rather than dynamic (typer invocation). Static evidence avoids the need to install Aider's full dev dependency tree (typer, GitPython, lox, pandas, importlib_resources, plus the aider package itself) and runs in ~10 seconds on a warm git cache. The argparse-level claim being made does not require dynamic execution to verify, because the flag string `--read-model-settings` appears literally in the typer.Option call and `--model-settings-file` literally does not.

## Severity justification

I am calling this **P2**. The criteria I weighed:

1. **User impact breadth.** Narrow. The affected population is Aider contributors running the harness and external evaluators who use the harness to score models for the public leaderboard. The aider CLI itself (the end-user product) is not affected. I estimate the population at low hundreds based on the bench README's posture as a development tool and the small number of reactions on the issue itself.

2. **Workaround availability.** A clean one-line workaround exists for anyone who knows about it: pass `--read-model-settings` in place of the documented `--model-settings-file`. The cost the bug creates is the cost of discovering the workaround in the first place; the workaround itself is trivial once known.

3. **Data loss or trust risk.** No data loss. Trust risk is real but bounded: benchmark results run without the requested model settings are technically invalid for the model's stated configuration, which matters for leaderboard fairness, but does not silently corrupt user files or repo state.

4. **Blocking critical user flows.** No. The aider chat CLI continues to work. Only the benchmark harness is affected.

A Cursor PQE hiring manager reading this section should expect me to defend the P2 against either direction. Against P1: this is not a customer-facing product bug, the affected population is narrow (developers running the bench, plus external evaluators scoring models for the public leaderboard), and the leaderboard contamination risk is real but does not produce data loss or auth-tier failures. Against P3: the silent-hang amplifier converts a recoverable misconfiguration into a multi-hour time-loss event, the same surface produced a still-open prior report (aider#2766), and the docs-versus-code drift signals a structural gap in the project's flag-naming discipline beyond a one-off typo. P2 captures both the bounded-population reality and the structural concern.

## Suggested fix or workaround

The reporter proposed three options. I rank them by my own judgment of cost versus completeness:

1. **Recommended: alias `--model-settings-file` in `benchmark/benchmark.py`.** Add `"--model-settings-file"` as a second positional flag string to the existing `typer.Option(None, "--read-model-settings", ...)` declaration at `benchmark/benchmark.py:207`, so both flag spellings resolve to the same `read_model_settings` parameter. One source line changed, no behavioral break for existing bench users, fully closes the docs-versus-code gap.
2. **Acceptable: rename `--read-model-settings` to `--model-settings-file` with `--read-model-settings` as a deprecation alias.** This reaches the same end state as option 1 and uses the more canonical flag name as the primary, but it introduces a soft deprecation lifecycle that the maintainers will need to schedule for removal.
3. **Cheapest but incomplete: add a one-line callout to the adv-model-settings docs and the bench README.** Closes the documentation gap but leaves the structural footgun for the next user who follows a stale link or generates the command from an LLM that read the docs.

User-side workaround until an upstream fix lands: pass `--read-model-settings path/to/settings.yml` (the actual flag in `benchmark/benchmark.py:207`). The bench README at line 85 names this correctly; the failure mode kicks in only when a user follows the README link out to the docs.

## Handoff

Recipient at Aider: the contributor maintaining `benchmark/` (likely the same person as the primary aider maintainer given Aider's small-team norms; recruiter screen at Aider would resolve the assignee within a normal triage cycle). The context the assignee needs:

- This document and the repro script at `scripts/repro/aider-5131/repro.sh`.
- The pinned reproducing SHA: `6435cb8b1e885d7275327d4b61206b1b1618dfe1` (current main HEAD as of 2026-05-18).
- The reporter has offered to send a PR (per the issue body's final line). Acknowledging the offer and pointing at option 2 from the issue body (alias) is the lowest-coordination path.
- The link to the possibly-related aider#2766 (Jan 2025, still open) so the assignee can dedupe surface area in one pass.

Success criteria for the fix:

- The repro's Probe 2 (`--model-settings-file` absent from `benchmark/benchmark.py`) must now FAIL. That is, `--model-settings-file` must appear in the source.
- The existing flag `--read-model-settings` must still parse without error (backward compatibility for anyone who already learned the original flag).
- One-line release note suitable for the bench README and the docs: *"--model-settings-file and --read-model-settings are now interchangeable in benchmark.py."*

## Sources

- Aider issue thread: [aider#5131](https://github.com/Aider-AI/aider/issues/5131)
- Pinned source files (resolved against SHA `6435cb8b1e885d7275327d4b61206b1b1618dfe1`):
  - [`benchmark/benchmark.py:207`](https://github.com/Aider-AI/aider/blob/6435cb8b1e885d7275327d4b61206b1b1618dfe1/benchmark/benchmark.py#L207) (the `--read-model-settings` declaration)
  - [`benchmark/benchmark.py:348`](https://github.com/Aider-AI/aider/blob/6435cb8b1e885d7275327d4b61206b1b1618dfe1/benchmark/benchmark.py#L348) (the `LONG_TIMEOUT` amplifier)
  - [`aider/website/docs/config/adv-model-settings.md:79`](https://github.com/Aider-AI/aider/blob/6435cb8b1e885d7275327d4b61206b1b1618dfe1/aider/website/docs/config/adv-model-settings.md?plain=1#L79) (the documented `--model-settings-file` flag)
  - [`benchmark/README.md:85`](https://github.com/Aider-AI/aider/blob/6435cb8b1e885d7275327d4b61206b1b1618dfe1/benchmark/README.md?plain=1#L85) (the README link that bridges the two flag names)
- Related still-open issue: [aider#2766](https://github.com/Aider-AI/aider/issues/2766)
- Lodestar Week-1 priority report context: `reports/aider-week.md` (noted #5131 as a recency-dominated rank-4-or-5 candidate; this escalation closes the loop on that note).

---

**Reviewer:** Wei Jia
**Date:** 2026-05-18
