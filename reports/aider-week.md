# Aider priority report, Week 1, 2026-05-18 generated

> **Source:** `reports/aider-week.csv` (CSV with empty rationale columns).
> **Pipeline:** ingest -> dedup -> moderate -> rank -> rationale_csv. Aider
> 90-day window, full observed open-issue population.
> **What this is:** the top 3 candidates the ranker surfaced, with Wei's
> rationale, severity assessment, and suggested action on each.
> **What this isn't:** an exhaustive review, a severity classification by
> the pipeline, or a multi-week trend report (multi-week is v0.1).

## Methodology one-paragraph reminder

The ranker scores each issue by `composite_score = w_engagement * engagement +
w_recency * recency + w_label * label_weight`, with default weights documented
in `voc/rank/score.py:RankConfig` and label weights in
`voc/rank/signals.py:LABEL_WEIGHTS`. Engagement is `log1p(comments + reactions)`
normalized to [0,1]. Recency is half-life decay from `updated_at`. Label
weight is an unweighted max over configured label categories. Score is a
candidate-priority signal for human review, not a severity assignment.

## Top 3 candidates

---

### #1 Python 3.13 support

- **Link:** https://github.com/Aider-AI/aider/issues/3037
- **Composite score:** 0.654 (recency 0.64 + engagement 0.99 + label 0.00)
- **Engagement:** 30 comments, 22 reactions, state open
- **Labels:** enhancement
- **PII flags:** none

**Wei's rationale (~150 words):**

There was a lot of community engagement on this topic, a lot of it that sounds like general confusion and just needing to be pointed to the right tooling. The engagement signal the ranker rewarded here is partly noise, because two comments from funtimefranky1530-coder in late January 2026 dump fake-physics equations into the thread and the reactions on those comments inflate the count without indicating priority. The most recent substantive comment, from akostadinov eight days ago, says the issue can be closed because `uv tool install` works on Python 3.14 via PR 4899.

**Severity assessment:** medium

**Suggested action:** Test that PR 4899 resolves the install path on Python 3.13 specifically. Once confirmed, the issue should be able to be closed.

**Reviewer:** Wei Jia

---

### #2 Reconsider Inclusion of Dependencies in Repo Map

- **Link:** https://github.com/Aider-AI/aider/issues/3603
- **Composite score:** 0.543 (recency 0.39 + engagement 0.97 + label 0.00)
- **Engagement:** 14 comments, 24 reactions, state open
- **Labels:** (none)
- **PII flags:** none

**Wei's rationale (~150 words):**

This was a valuable add and a real feature request to unblock users and improve aider functionality. Eng work is already done by [an external contributor](https://github.com/csrocha/aider/tree/git-submodules) and the maintainer just needs to review and merge. ([Named user blocker](https://github.com/Aider-AI/aider/issues/3603#issuecomment-3856238373) from February 2026.)

**Severity assessment:** high

**Suggested action:** Only testing and validation left for this.

**Reviewer:** Wei Jia

---

### #3 Zed Editor Support

- **Link:** https://github.com/Aider-AI/aider/issues/851
- **Composite score:** 0.474 (recency 0.67 + engagement 0.52 + label 0.00)
- **Engagement:** 10 comments, 0 reactions, state open
- **Labels:** enhancement
- **PII flags:** none

**Wei's rationale (~150 words):**

This is a future roadmap item, supporting [ACP](https://agentclientprotocol.com/overview/introduction) (Agent Client Protocol) and thus GUI for aider. The tool in its current form, as CLI, is useful for most and likely targets a very specific subset of users. ([Community PR 4936](https://github.com/Aider-AI/aider/pull/4936) already exists as a head start when the time comes.)

**Severity assessment:** low

**Suggested action:** As the roadmap widens and there is more capacity to support a wider range of users, this feature should be explored. But it's a backlog item for now.

**Reviewer:** Wei Jia

---

## Where the pipeline and human judgment diverged

Across all three issues the ranker placed at the top, the comment threads share a structural pattern the pipeline does not pick up. Two of the three (issues 3603 and 851) have community-built PRs or forks with working code waiting on maintainer review, and the third (3037) has a recent comment claiming an upstream fix has already shipped via PR 4899. The composite ranker scores these on engagement and recency but not on PR-readiness or whether the bottleneck is engineering work versus maintainer attention. From a PQE judgment standpoint, this is the kind of signal that would change my handoff recommendation, because when the community has done the work the action is to triage the open PR and unblock the merge, not to investigate the problem from scratch. The ranker's top three would benefit from a `community_pr_open` boolean signal that the GitHub Issues schema can surface cheaply and the dedup/rank pipeline does not currently track. A second pipeline-design observation surfaced in the rank-4 and rank-5 rows: issue 5131 (a docs-versus-CLI flag mismatch, two comments, zero reactions) and issue 5145 (an uncaught `NotImplementedError` in `pathlib.py`, already closed) both surfaced in the top five despite weak engagement, which suggests recency dominates more than I expected at this window and that filtering closed issues out of the candidate pool before ranking is a v0.1 candidate.

## Limitations of this week's report

This week's report runs against the open-issue population only by composite score, with no filter for issue state or for the presence of an existing PR. The engagement signal is unweighted across comment authors, which means a thread inflated by spam reactions (see issue 3037) scores the same as a thread of substantive technical discussion. Single-tool, single-week scope by design; multi-week trend and cross-tool synthesis are v0.1 work.
