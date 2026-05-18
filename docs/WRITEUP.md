# lodestar — a public-source VoC v0 for agentic coding tools

> **Status:** [TEMPLATE — Wei to fill the prose. Section headers and honest-framing
> sentences are skeletal; Wei writes 200-400 words per section in his voice.]

## What this is

[~150 words. Lodestar is a public, reproducible Voice-of-Customer v0 for
three agentic coding tools (Aider, Cline, Continue). It ingests GitHub
issues, deduplicates, surfaces a curated top-20 weekly, and a human writes
the priority-5 rationale. Voice synthesis pulls public discussion from
GitHub issues, Reddit r/ChatGPTCoding, and Hacker News. The escalation
pillar demonstrates a Playwright bug reproduction handed off to a
maintainer with a documented response loop.]

## What this isn't

[~100 words. Per Wei's README:

- Not a production VoC tool
- Not a statistically powered study (no sampling claim, no significance testing, no IRR)
- Not an auto-severity-classifier (severity is human judgment by design)
- Not a customer support intake tool (ClearFlask is that)
- Not a "first 30 days at Cursor" framing (presumptuous)]

## Methodology

[~300 words. Descriptive only — no sampling claim, full observed weekly population
over a 4-week rolling window per Pass 4.5 (Aider 53/wk window, Cline 162/wk window,
Continue 106/wk window). Dedup is fuzzy-title (rapidfuzz token_set_ratio @ 0.85)
plus semantic-similarity (TF-IDF cosine @ 0.5) clustered with union-find. Moderation
is deterministic PII regex (load-bearing) plus Haiku 4.5 LLM augmentation
(bypassable, not load-bearing). Ranker is engagement × recency × label_weight with
an auditable per-issue breakdown. Label weights are defensible operator wisdom,
not calibrated against ground truth (none exists for this data). Theme clustering
is TF-IDF + KMeans, descriptive only. Every quoted issue field passes through
the PII filter.]

## What I learned about each tool

[~500 words total, ~165 per tool. Wei's actual observations from reading
2 weeks of priority reports + the voice synthesis memos. Cite specific
issue IDs and quotes. Distinguish "I observed" from "I conclude".]

### Aider

[2-3 specific patterns observed; cite real issue IDs from the Week-N priority report.]

### Cline

[same shape]

### Continue

[same shape; note the 4-week-volume drop vs 12-week-average and offer
the skeptical reading per Wei's pick on adversarial review check #3.]

## Honest limitations

[~250 words. The Aider 53-issue pool is small (top-20 surfaces 38% of corpus).
Discord is excluded because login-gated. No customer interviews because no
public-recruit network and proprietary data is IP-locked. LLM moderation is
bypassable via prompt injection (deterministic PII is the load-bearing gate).
The label weights are unvalidated. The score formula is one defensible choice
among many. v0 is descriptive, not inferential.]

## What I'd do at Cursor with private telemetry

[~400 words. Thesis: lodestar's public-source synthesis is half of what a Cursor
PQE could ship publicly. The other half is the private signal — support tickets,
in-product telemetry, Discord-server volume, paid-tier churn correlations.
Wei's plan for combining the two: per-source confidence scores, weighted toward
private signal where available, public-only fallback for cold-start segments.
Honest about what's missing: lodestar can't demonstrate the private half until
Cursor hires me.]
