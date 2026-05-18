"""Per-signal scoring functions for the ranker.

Pure functions over a single Issue. No shared state. Each function returns
a float in [0, 1] that the composer in voc.rank.score weights into the
composite candidate-priority score.

Design notes:

- recency uses 2 ** (-age/half_life) rather than exp(-age/T) so the
  half-life parameter is directly interpretable to reviewers without
  unit conversion.
- engagement uses log1p compression so a heavy-tailed mega-thread does
  not dominate the score.
- label is a clamped weighted sum so a single P0/crash/regression
  saturates without compounding.
"""
from __future__ import annotations

import math
from collections.abc import Mapping
from datetime import datetime

from voc.schema.issue import Issue


def recency_score(issue: Issue, now: datetime, half_life_days: float) -> float:
    """Exponential decay over (now - issue.updated_at).

    Returns a value in [0, 1]. Future-dated updated_at clamps to 1.0
    so clock skew or future-dated fixtures cannot produce >1. With
    half_life_days=14: a fresh issue scores 1.0, a 2-week-old issue
    scores 0.5, a 4-week-old issue scores 0.25.

    Uses base-2 exponent (rather than e) so the parameter is the
    actual half-life in days.
    """
    age_seconds = (now - issue.updated_at).total_seconds()
    if age_seconds <= 0:
        return 1.0
    age_days = age_seconds / 86400.0
    return 2.0 ** (-age_days / half_life_days)


def engagement_score(issue: Issue, reaction_weight: float, ceiling: float) -> float:
    """log1p-normalized engagement signal.

    raw = comments_count + reaction_weight * reactions_count
    score = log1p(raw) / log1p(ceiling), clamped to [0, 1].

    Reactions weighted higher than comments because reactions require a
    deliberate click and cannot be off-topic; comments often carry noise.
    log1p compression keeps a 100-engagement issue from dominating a
    10-engagement one. Reaction weight and ceiling are configurable.
    """
    raw = issue.comments_count + reaction_weight * issue.reactions_count
    if raw <= 0 or ceiling <= 0:
        return 0.0
    score = math.log1p(raw) / math.log1p(ceiling)
    return min(score, 1.0)


def label_score(issue: Issue, weights: Mapping[str, float], label_max: float) -> float:
    """Sum of weights for labels present on the issue, clamped to label_max.

    Labels are matched case-insensitively. Unknown labels contribute 0.
    Result is in [0, 1] when label_max > 0.

    A single high-priority label (P0, crash, data-loss) should saturate
    the component; piling on additional labels does not compound past
    the max. This discourages label-spam gaming.
    """
    if label_max <= 0:
        return 0.0
    matched = sum(weights.get(label.lower(), 0.0) for label in issue.labels)
    return min(matched / label_max, 1.0)
