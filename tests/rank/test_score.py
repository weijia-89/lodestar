"""Tests for RankConfig and the composite score_issue function.

Task 4 of docs/superpowers/plans/2026-05-17-ranker.md.
"""
import dataclasses
import random
from datetime import timedelta

import pytest

from voc.rank.score import RankConfig, ScoreBreakdown, score_issue

# `dataclasses` is referenced inside a pytest.raises tuple below; the import
# is structurally necessary even though ruff's static-use detector may miss it.
_ = dataclasses


def test_rank_config_defaults_sum_to_one():
    """Weights compose into a [0, 1] composite, so the defaults must sum to 1.

    A future contributor changing the defaults should see this fail and
    deliberately update both the default values and any callers that
    depend on the [0, 1] composite range.
    """
    c = RankConfig()
    assert c.w_recency + c.w_engagement + c.w_label == pytest.approx(1.0)


def test_score_issue_returns_score_breakdown_with_issue_id(make_issue, now):
    issue = make_issue(1)
    breakdown = score_issue(issue, now, RankConfig())
    assert isinstance(breakdown, ScoreBreakdown)
    assert breakdown.issue_id == "aider:1"


def test_composite_is_weighted_sum_of_components(make_issue, now):
    """composite must equal w_r*recency + w_e*engagement + w_l*label."""
    cfg = RankConfig()
    issue = make_issue(
        1,
        labels=["bug"],
        comments_count=5,
        reactions_count=2,
        updated_at=now - timedelta(days=7),
    )
    b = score_issue(issue, now, cfg)
    expected = (
        cfg.w_recency * b.recency
        + cfg.w_engagement * b.engagement
        + cfg.w_label * b.label
    )
    assert b.composite == pytest.approx(expected, rel=1e-9)


def test_composite_in_bounds_random(make_issue, now):
    """For any valid Issue, composite must be in [0, 1]."""
    random.seed(7)
    for i in range(20):
        issue = make_issue(
            i,
            comments_count=random.randint(0, 200),
            reactions_count=random.randint(0, 100),
            labels=random.sample(
                ["bug", "crash", "p0", "enhancement"], k=random.randint(0, 3)
            ),
            updated_at=now - timedelta(days=random.randint(0, 60)),
        )
        b = score_issue(issue, now, RankConfig())
        assert 0.0 <= b.composite <= 1.0, f"out of bounds at i={i}: {b}"


def test_score_breakdown_is_frozen_dataclass():
    """ScoreBreakdown must be immutable for safe parquet round-trip and caching."""
    b = ScoreBreakdown(
        issue_id="x:1", recency=0.5, engagement=0.5, label=0.5, composite=0.5
    )
    with pytest.raises((AttributeError, TypeError, dataclasses.FrozenInstanceError)):
        b.recency = 0.7  # type: ignore[misc]


def test_higher_recency_higher_composite_holding_others_constant(make_issue, now):
    cfg = RankConfig()
    old = score_issue(make_issue(1, updated_at=now - timedelta(days=30)), now, cfg)
    new = score_issue(make_issue(2, updated_at=now - timedelta(days=1)), now, cfg)
    assert new.composite > old.composite


def test_score_issue_with_p0_label_outscores_unlabeled(make_issue, now):
    """Holding recency + engagement constant, a P0 label should raise the composite."""
    cfg = RankConfig()
    base = score_issue(make_issue(1, updated_at=now, labels=[]), now, cfg)
    p0 = score_issue(make_issue(2, updated_at=now, labels=["p0"]), now, cfg)
    assert p0.composite > base.composite
