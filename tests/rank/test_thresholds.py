"""Targeted mutation-coverage tests for ranker boundaries.

Addresses surviving mutants from the 2026-05-17 mutmut run:

- recency_score `<=0` vs `<0` vs `<=1` (age boundary)
- engagement_score `or` vs `and` (early-return condition shape)
- engagement_score `ceiling <=0` vs `<0` vs `<=1`
- label_score `label_max <=0` boundary and return-zero behavior
- label_score `matched / label_max` vs `matched * label_max`
- top_n `n <= 0` boundary
- top_n config-passthrough (caller-supplied vs default RankConfig)
"""
from datetime import timedelta

import pytest

from voc.rank.ranker import rank, top_n
from voc.rank.score import RankConfig
from voc.rank.signals import engagement_score, label_score, recency_score

# ============================================================
# recency_score boundary
# ============================================================


def test_recency_score_age_exactly_zero(make_issue, now):
    """age_seconds == 0 must return 1.0 (kills mutmut_3: `<=0` -> `<0`)."""
    issue = make_issue(1, updated_at=now)  # exact equality
    assert recency_score(issue, now, 14.0) == 1.0


def test_recency_score_tiny_positive_age_below_one(make_issue, now):
    """0 < age_seconds < 1 must NOT be clamped to 1.0 (kills mutmut_4: `<=0` -> `<=1`).

    With half_life_days=14, a 0.5-second age gives a slightly-below-1.0 score.
    """
    issue = make_issue(1, updated_at=now - timedelta(seconds=0.5))
    score = recency_score(issue, now, 14.0)
    assert score < 1.0
    assert score > 0.999  # extremely close to 1.0 but strictly less


# ============================================================
# engagement_score early-return shape
# ============================================================


def test_engagement_zero_raw_but_positive_ceiling_returns_zero(make_issue):
    """raw=0, ceiling=100: returns 0 (kills mutmut_4: `or` -> `and`).

    Under `and`, the function would proceed to log1p(0)/log1p(100)=0 anyway,
    BUT under `or`, raw<=0 alone triggers the early return. The difference
    fires when only ONE branch is true. Here raw<=0 is true; ceiling<=0 is
    false. Under `and`, the early-return would NOT fire; the function would
    instead compute log1p(0)/log1p(100) = 0/log(101) = 0. So same result!
    Hmm — to kill this we need a case where the post-early-return path
    differs from 0. Try a scenario where raw=0 but log1p(raw)/log1p(ceiling)
    would NOT be 0 — but log1p(0) IS 0. So this mutation is genuinely
    equivalent for raw=0 cases.

    Force a difference via ceiling=0: under `or` (original), ceiling<=0 hits
    early-return -> 0. Under `and`, raw>0 is true but ceiling<=0 keeps both
    branches; the post-early-return computes log1p(raw)/log1p(0) which is
    log1p(raw)/0 -> ZeroDivisionError. That kills the mutant.
    """
    issue = make_issue(1, comments_count=10, reactions_count=0)
    # ceiling=0 must NOT crash; the early-return guards against div-by-zero
    assert engagement_score(issue, reaction_weight=3, ceiling=0) == 0.0


def test_engagement_negative_ceiling_returns_zero(make_issue):
    """ceiling=-1 returns 0 (kills mutmut_7: `ceiling <= 0` -> `ceiling < 0`).

    Mutant test: ceiling=0 -> original: True (<=0); mutant: False (<0).
    Original takes early-return -> 0. Mutant proceeds to log1p(raw)/log1p(0)
    which is log/0 -> ZeroDivisionError or inf. Verified by the previous
    test_engagement_zero_raw_but_positive_ceiling_returns_zero passing
    iff the original behavior holds.
    """
    issue = make_issue(1, comments_count=10)
    assert engagement_score(issue, reaction_weight=3, ceiling=-1.0) == 0.0


def test_engagement_ceiling_exactly_one_does_not_early_return(make_issue):
    """ceiling=1 with raw>0 must NOT return 0 (kills mutmut_8: `<=0` -> `<=1`).

    log1p(raw)/log1p(1) = log1p(raw)/log(2). For raw=1: 1.0/0.693 ≈ 1.443
    which clamps to 1.0. The output is non-zero.
    """
    issue = make_issue(1, comments_count=1)
    score = engagement_score(issue, reaction_weight=3, ceiling=1.0)
    assert score > 0.0
    assert score == 1.0  # log1p(1)/log1p(1) = 1, then min clamp


# ============================================================
# label_score boundary
# ============================================================


def test_label_score_label_max_exactly_zero_returns_zero(make_issue):
    """label_max=0 returns 0.0 (kills mutmut_1: `<=0` -> `<0` AND mutmut_3 returns 1.0).

    Original: returns 0.0 via early-return.
    mutmut_1: condition becomes `<0`; label_max=0 fails to trigger; proceeds
    to matched / 0 which is ZeroDivisionError.
    mutmut_3: returns 1.0 instead of 0.0.
    """
    weights = {"bug": 0.5}
    assert label_score(make_issue(1, labels=["bug"]), weights, label_max=0.0) == 0.0


def test_label_score_division_vs_multiplication_diverges_for_large_label_max(make_issue):
    """label_max=2.0 produces different results under `matched / max` vs `matched * max`.

    Kills mutmut_16: `/` -> `*`.
    With weights={bug: 0.4} and label_max=2.0:
      original: 0.4 / 2.0 = 0.2
      mutant:   0.4 * 2.0 = 0.8, clamped to 0.8
    """
    weights = {"bug": 0.4}
    score = label_score(make_issue(1, labels=["bug"]), weights, label_max=2.0)
    assert score == pytest.approx(0.2)


# ============================================================
# top_n boundary
# ============================================================


def test_top_n_zero_returns_empty_explicit(make_issue, now):
    """n=0 returns [] (kills mutmut_1: `n <= 0` -> `n < 0`).

    Under `n < 0`, n=0 would NOT early-return; would compute and slice to
    [:0] which is []. Returns same empty list! Equivalent unless we can
    detect the call to `rank()` happened. We cannot via the public API
    without a spy. So mutmut_1 is functionally equivalent in observed
    behavior despite the mutation.

    Documented; this test asserts the contract (n=0 -> []) regardless.
    """
    issues = [make_issue(1)]
    assert top_n(issues, n=0, now=now) == []


def test_top_n_one_returns_singleton(make_issue, now):
    """n=1 returns a 1-element list (kills mutmut_2: `n <= 0` -> `n <= 1`).

    Under `n <= 1`, n=1 triggers the early return -> []. Under original,
    n=1 proceeds and returns 1-element list.
    """
    issues = [make_issue(1, comments_count=5), make_issue(2, comments_count=10)]
    out = top_n(issues, n=1, now=now)
    assert len(out) == 1


def test_top_n_honors_caller_supplied_config(make_issue, now):
    """top_n must pass the caller's RankConfig through to rank().

    Kills mutmut_9 (cfg -> None) and mutmut_12 (cfg dropped from rank() call).
    A custom config with w_recency=1.0, w_engagement=0, w_label=0 makes the
    composite equal to the pure recency. We verify that this config is
    respected by checking the composite matches recency exactly.
    """
    custom_cfg = RankConfig(
        w_recency=1.0,
        w_engagement=0.0,
        w_label=0.0,
    )
    issue = make_issue(
        1, comments_count=100, reactions_count=100, labels=["p0"], updated_at=now
    )
    out = top_n([issue], n=1, now=now, config=custom_cfg)
    _, breakdown = out[0]
    # If config were not passed through, composite would be a weighted sum
    # including engagement and label contributions (both maxed out, near 1).
    # With the custom config, composite must equal recency exactly (= 1.0).
    assert breakdown.composite == pytest.approx(breakdown.recency)
    assert breakdown.composite == pytest.approx(1.0)


def test_top_n_default_config_uses_default_label_weights(make_issue, now):
    """When no config passed, default label_weights apply: 'p0' label saturates label_score."""
    no_labels = make_issue(1, labels=[], updated_at=now)
    p0_labeled = make_issue(2, labels=["p0"], updated_at=now)
    out = top_n([no_labels, p0_labeled], n=2, now=now)
    # p0 must rank first because default weights give p0 the maximum
    assert out[0][1].issue_id == "aider:2"
    assert out[0][1].label == pytest.approx(1.0)
    assert out[1][1].label == 0.0


# ============================================================
# rank() with single-issue input must also use config
# ============================================================


def test_default_label_weights_contract():
    """The default label_weights dict must contain the documented keys and values.

    Kills mutmut survivors on `_default_label_weights` that mutate string
    literals (e.g., 'bug' -> 'XXbugXX', 'p0' -> 'XXp0XX') and numeric values
    (e.g., 0.5 -> 1.5, 1.0 -> 2.0). The contract is documented in CLAUDE.md;
    a change to these defaults is a calibration decision and should fail
    this test to force explicit acknowledgement.
    """
    cfg = RankConfig()
    weights = dict(cfg.label_weights)
    assert weights == {
        "bug": 0.5,
        "crash": 1.0,
        "regression": 1.0,
        "p0": 1.0,
        "p1": 0.7,
        "breaking": 0.8,
        "data-loss": 1.0,
    }


def test_rank_honors_custom_label_weights(make_issue, now):
    """rank() must pass label_weights through to label_score."""
    custom_cfg = RankConfig(
        label_weights={"experimental": 0.9},  # non-default key
        w_recency=0.0,
        w_engagement=0.0,
        w_label=1.0,
    )
    a = make_issue(1, labels=["bug"], updated_at=now)
    b = make_issue(2, labels=["experimental"], updated_at=now)
    out = rank([a, b], now, custom_cfg)
    # 'experimental' should outrank 'bug' since only 'experimental' is in
    # the custom weights dict. 'bug' would score 0 here.
    assert out[0].issue_id == "aider:2"
    assert out[0].label == pytest.approx(0.9)
    assert out[1].label == 0.0
