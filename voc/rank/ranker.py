"""Top-N candidate ranker over a Sequence[Issue].

Sort order: composite_score descending, ties broken by issue.id ascending.
The deterministic tiebreaker is load-bearing for the invariance properties
in tests/rank/test_invariants.py.
"""
from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from voc.rank.score import RankConfig, ScoreBreakdown, score_issue
from voc.schema.issue import Issue


def rank(
    issues: Sequence[Issue],
    now: datetime,
    config: RankConfig | None = None,
) -> list[ScoreBreakdown]:
    """Return ScoreBreakdowns sorted by composite descending, ties by issue.id ascending."""
    cfg = config or RankConfig()
    breakdowns = [score_issue(i, now, cfg) for i in issues]
    breakdowns.sort(key=lambda b: (-b.composite, b.issue_id))
    return breakdowns


def top_n(
    issues: Sequence[Issue],
    n: int,
    now: datetime,
    config: RankConfig | None = None,
) -> list[tuple[Issue, ScoreBreakdown]]:
    """Top-N (Issue, ScoreBreakdown) pairs, sorted by composite descending.

    Returns [] if n<=0 or issues is empty. Caps at population size if n
    exceeds it.
    """
    if n <= 0:
        return []
    cfg = config or RankConfig()
    by_id = {i.id: i for i in issues}
    breakdowns = rank(issues, now, cfg)[:n]
    return [(by_id[b.issue_id], b) for b in breakdowns]
