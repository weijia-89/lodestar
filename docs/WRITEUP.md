# lodestar, a public-source VoC v0-min for agentic coding tools

> **Status:** [TEMPLATE, v0-min ~500 words. Wei to fill each section's body
> from the actual Aider Week-N priority report. Word budgets are guidance,
> not hard limits.]

## What this is (~75 words)

[Lodestar is a public, reproducible Voice-of-Customer v0-min for Aider.
The pipeline ingests Aider's GitHub Issues, deduplicates, flags PII, ranks
the open-issue population by engagement * recency * label_weight, and emits
a top-20 candidate list. The human (Wei) writes rationale on the top 3.
The pipeline is supporting infrastructure; the priority report with rationale
is the demonstration. v0.1 extends to Cline + Continue, adds voice synthesis
from Reddit + HN, and a worked escalation.]

## What this isn't (~50 words)

[v0-min ships one tool (Aider), one week, top-3 rationales. The scope-cut
is honest:

- Not a production VoC system
- Not a statistically powered study (no sampling claim, no significance testing, no inter-rater reliability)
- Not an auto-severity classifier (severity stays human judgment)
- Not a multi-tool or multi-week trend report

Voice synthesis (Reddit + HN), TF-IDF theme clustering, and a worked
Playwright escalation are v0.1.]

## Methodology (~100 words)

[Descriptive only, no sampling claim, full observed 90-day Aider issue
population. Dedup is fuzzy-title (rapidfuzz token_set_ratio at 0.85) plus
semantic similarity (TF-IDF cosine at 0.5), clustered with union-find.
Moderation is deterministic PII regex (load-bearing, zero mutation
survivors). Ranker is engagement * recency * label_weight with an
auditable per-issue ScoreBreakdown. Label weights are defensible operator
wisdom, not calibrated against ground truth (none exists for this
data). Every quoted field passes the PII filter. 76% mutation kill rate
on dedup + rank + moderate + report.]

## What I learned about Aider (~150 words)

[Wei's specific observations from reading the top-20 + writing rationale
on top-3. Cite issue IDs. State 2-3 patterns. Distinguish "I observed"
(direct, single-week) from "I conclude" (multi-week or cross-source,
which v0-min does not support). Note one issue that the ranker scored
high but Wei disagreed with on review (or note that the top-3 all
landed where Wei would have ranked them by hand). The "where the
pipeline and human judgment diverged" observation is the PQE-shape
content reviewers should read.]

## Honest limitations (~100 words)

[v0-min covers one tool, one week, top-3 rationales. No cross-tool, no
multi-week, no voice synthesis, no worked escalation. The Aider open
population is the corpus; closed issues are out of scope. LLM moderation
augmentation is not in v0-min (regex is the load-bearing PII gate; LLM
augmentation is bypassable and would have been advisory at best). Label
weights are unvalidated against any merge-vs-close rate. The score
formula is one defensible choice; calibration against real per-tool
ground truth is v0.2 work.]

## What I'd do at Cursor with private telemetry (~75 words)

[Lodestar's public-source synthesis is half of what a Cursor PQE could
ship internally. The other half is private signal: support tickets,
in-product telemetry, Discord volume, paid-tier churn correlations.
Plan: per-source confidence scores, weighted toward private signal where
available, public-only fallback for cold-start segments. Honest about
what's missing, I cannot demonstrate the private half from outside
Cursor.]
