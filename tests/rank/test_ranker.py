"""Tests for the ranker: rank() and top_n() over a Sequence[Issue].

Task 5 of docs/superpowers/plans/2026-05-17-ranker.md.
"""
from datetime import timedelta

from voc.rank.ranker import rank, top_n


def test_rank_empty_input_returns_empty_list(now):
    assert rank([], now) == []


def test_rank_single_issue_returns_singleton(make_issue, now):
    out = rank([make_issue(1)], now)
    assert len(out) == 1
    assert out[0].issue_id == "aider:1"


def test_rank_sorts_by_composite_descending(make_issue, now):
    old = make_issue(1, updated_at=now - timedelta(days=60), labels=[])
    new_high_engagement = make_issue(
        2,
        updated_at=now,
        labels=["bug"],
        comments_count=10,
        reactions_count=5,
    )
    mid = make_issue(3, updated_at=now - timedelta(days=7), labels=[], comments_count=2)
    out = rank([old, new_high_engagement, mid], now)
    composites = [b.composite for b in out]
    assert composites == sorted(composites, reverse=True)
    assert out[0].issue_id == "aider:2"


def test_rank_ties_broken_by_issue_id_ascending(make_issue, now):
    """Two issues identical except for id sort by id ascending."""
    a = make_issue(2)  # aider:2
    b = make_issue(1)  # aider:1
    out = rank([a, b], now)
    assert [r.issue_id for r in out] == ["aider:1", "aider:2"]


def test_rank_is_deterministic_across_repeated_calls(make_issue, now):
    issues = [
        make_issue(
            i,
            comments_count=i,
            reactions_count=i % 3,
            labels=["bug"] if i % 2 else [],
        )
        for i in range(20)
    ]
    runs = [tuple(b.issue_id for b in rank(issues, now)) for _ in range(10)]
    assert len(set(runs)) == 1


def test_top_n_returns_n_pairs(make_issue, now):
    issues = [make_issue(i, comments_count=i) for i in range(10)]
    top = top_n(issues, n=3, now=now)
    assert len(top) == 3
    for issue, breakdown in top:
        assert breakdown.issue_id == issue.id


def test_top_n_caps_at_population_size(make_issue, now):
    issues = [make_issue(i) for i in range(3)]
    top = top_n(issues, n=20, now=now)
    assert len(top) == 3


def test_top_n_with_zero_returns_empty(make_issue, now):
    issues = [make_issue(i) for i in range(3)]
    assert top_n(issues, n=0, now=now) == []
