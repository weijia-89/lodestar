"""Tests for per-signal scoring functions (recency, engagement, label).

Tasks 1-3 of docs/superpowers/plans/2026-05-17-ranker.md.
"""
import random
from datetime import timedelta

import pytest

from voc.rank.signals import engagement_score, label_score, recency_score

# ============================================================
# Task 1: recency_score
# ============================================================


def test_recency_score_zero_age_is_one(make_issue, now):
    issue = make_issue(1, updated_at=now)
    assert recency_score(issue, now, half_life_days=14) == 1.0


def test_recency_score_half_life_age_is_half(make_issue, now):
    issue = make_issue(1, updated_at=now - timedelta(days=14))
    assert recency_score(issue, now, half_life_days=14) == pytest.approx(0.5, rel=1e-9)


def test_recency_score_double_half_life_is_quarter(make_issue, now):
    issue = make_issue(1, updated_at=now - timedelta(days=28))
    assert recency_score(issue, now, half_life_days=14) == pytest.approx(0.25, rel=1e-9)


def test_recency_score_monotone_decreasing_in_age(make_issue, now):
    ages = [0, 1, 5, 14, 28, 60, 365]
    scores = [
        recency_score(make_issue(i, updated_at=now - timedelta(days=d)), now, 14)
        for i, d in enumerate(ages)
    ]
    assert scores == sorted(scores, reverse=True)


def test_recency_score_future_updated_clamped_to_one(make_issue, now):
    """Clock skew or test-fixture future timestamp must not produce >1.0."""
    issue = make_issue(1, updated_at=now + timedelta(days=1))
    assert recency_score(issue, now, half_life_days=14) == 1.0


# ============================================================
# Task 2: engagement_score
# ============================================================


def test_engagement_score_zero_engagement_is_zero(make_issue):
    issue = make_issue(1, comments_count=0, reactions_count=0)
    assert engagement_score(issue, reaction_weight=3, ceiling=100) == 0.0


def test_engagement_reactions_weighted_three_times_comments(make_issue):
    by_comments = make_issue(1, comments_count=3, reactions_count=0)
    by_reactions = make_issue(2, comments_count=0, reactions_count=1)
    assert (
        engagement_score(by_comments, reaction_weight=3, ceiling=100)
        == engagement_score(by_reactions, reaction_weight=3, ceiling=100)
    )


def test_engagement_score_uses_log1p_compression(make_issue):
    """High-engagement issues should compress, not dominate. The ratio between
    a 100-engagement and 10-engagement issue is less than the raw 10x.
    """
    a = make_issue(1, comments_count=10, reactions_count=0)
    b = make_issue(2, comments_count=100, reactions_count=0)
    ratio = engagement_score(b, 3, 100) / engagement_score(a, 3, 100)
    assert 1.5 < ratio < 5.0


def test_engagement_score_clamped_to_one(make_issue):
    """Engagement above the ceiling clamps to 1.0, not >1."""
    issue = make_issue(1, comments_count=10000, reactions_count=10000)
    assert engagement_score(issue, 3, 100) == 1.0


def test_engagement_score_in_bounds_for_random_inputs(make_issue):
    random.seed(42)
    for i in range(50):
        c = random.randint(0, 1000)
        r = random.randint(0, 1000)
        s = engagement_score(make_issue(i, comments_count=c, reactions_count=r), 3, 100)
        assert 0.0 <= s <= 1.0


# ============================================================
# Task 3: label_score
# ============================================================


def test_label_score_no_labels_is_zero(make_issue):
    weights = {"bug": 0.5, "crash": 1.0}
    assert label_score(make_issue(1, labels=[]), weights, label_max=1.0) == 0.0


def test_label_score_unknown_labels_are_zero(make_issue):
    weights = {"bug": 0.5, "crash": 1.0}
    assert label_score(make_issue(1, labels=["enhancement"]), weights, 1.0) == 0.0


def test_label_score_single_weighted_label(make_issue):
    weights = {"bug": 0.5, "crash": 1.0}
    assert label_score(make_issue(1, labels=["bug"]), weights, 1.0) == 0.5


def test_label_score_sums_multiple_labels_capped_at_max(make_issue):
    weights = {"bug": 0.5, "crash": 1.0}
    # bug + crash = 1.5, capped at label_max=1.0
    assert label_score(make_issue(1, labels=["bug", "crash"]), weights, 1.0) == 1.0


def test_label_score_case_insensitive(make_issue):
    """GitHub labels can vary in case; weight match must normalize."""
    weights = {"bug": 0.5}
    assert label_score(make_issue(1, labels=["BUG"]), weights, 1.0) == 0.5
    assert label_score(make_issue(2, labels=["Bug"]), weights, 1.0) == 0.5
