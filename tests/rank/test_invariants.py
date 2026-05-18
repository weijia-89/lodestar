"""Property tests for ranker invariants. Belt-and-suspenders for adversarial review.

Task 6 of docs/superpowers/plans/2026-05-17-ranker.md. Falsifier coverage:
- R5: determinism under input order (shuffle test)
- R7: empty/singleton handling (via test_ranker.py)
- Monotonicity: composite must move correctly with each component
"""
import random
from datetime import timedelta

from voc.rank.ranker import rank


def test_ranking_invariant_under_shuffle(make_issue, now):
    """Same issues in different input order produce the same ranking sequence."""
    random.seed(42)
    issues = [
        make_issue(
            i,
            comments_count=random.randint(0, 50),
            reactions_count=random.randint(0, 20),
            labels=random.sample(
                ["bug", "crash", "p0", "enhancement"], k=random.randint(0, 3)
            ),
            updated_at=now - timedelta(days=random.randint(0, 60)),
        )
        for i in range(30)
    ]
    baseline = [b.issue_id for b in rank(issues, now)]
    shuffled = issues[:]
    for _ in range(5):
        random.shuffle(shuffled)
        ranked = [b.issue_id for b in rank(shuffled, now)]
        assert ranked == baseline


def test_all_component_scores_in_bounds(make_issue, now):
    random.seed(7)
    issues = [
        make_issue(
            i,
            comments_count=random.randint(0, 500),
            reactions_count=random.randint(0, 300),
            labels=random.sample(
                ["bug", "crash", "p0", "p1", "data-loss"], k=random.randint(0, 3)
            ),
            updated_at=now - timedelta(days=random.randint(0, 365)),
        )
        for i in range(50)
    ]
    for b in rank(issues, now):
        assert 0.0 <= b.composite <= 1.0
        assert 0.0 <= b.recency <= 1.0
        assert 0.0 <= b.engagement <= 1.0
        assert 0.0 <= b.label <= 1.0


def test_increasing_engagement_monotonically_increases_composite(make_issue, now):
    """Holding recency and labels constant, more engagement does not decrease composite."""
    scores = []
    for c in [0, 1, 5, 20, 100]:
        b = rank(
            [make_issue(1, labels=[], updated_at=now, comments_count=c)], now
        )[0]
        scores.append(b.composite)
    assert scores == sorted(scores), f"non-monotone in engagement: {scores}"


def test_increasing_age_monotonically_decreases_composite(make_issue, now):
    """Holding engagement and labels constant, older issues do not score higher."""
    scores = []
    for days in [0, 1, 7, 14, 28, 60, 365]:
        issue = make_issue(
            1,
            comments_count=0,
            reactions_count=0,
            labels=[],
            updated_at=now - timedelta(days=days),
        )
        scores.append(rank([issue], now)[0].composite)
    assert scores == sorted(scores, reverse=True), f"non-monotone in age: {scores}"


def test_p0_label_outranks_unlabeled_holding_others_constant(make_issue, now):
    unlabeled = make_issue(1, labels=[], updated_at=now)
    p0 = make_issue(2, labels=["p0"], updated_at=now)
    out = rank([unlabeled, p0], now)
    assert out[0].issue_id == "aider:2"
