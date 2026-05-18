"""Composite scoring via RankConfig.

The composite is a weighted sum of three signals. Every component is
surfaced in ScoreBreakdown so reviewers can audit, override, and write
rationale rather than treating the composite as a stealth severity.

Per CLAUDE.md: severity remains human judgment. The composite is a
candidate-priority signal for sorting the candidate pool, not a severity
classification.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime

from voc.rank.signals import engagement_score, label_score, recency_score
from voc.schema.issue import Issue


def _default_label_weights() -> dict[str, float]:
    """Defaults are v0 priors. Calibrate against real per-tool label vocabularies
    by re-running the ranker against rationale-tagged top-5 selections from
    multiple weekly cycles.
    """
    return {
        "bug": 0.5,
        "crash": 1.0,
        "regression": 1.0,
        "p0": 1.0,
        "p1": 0.7,
        "breaking": 0.8,
        "data-loss": 1.0,
    }


@dataclass(frozen=True)
class RankConfig:
    """Configuration for the composite scorer.

    Defaults are v0 priors. The CLI accepts overrides via a JSON file
    (see voc/rank/__main__.py). Weights w_recency + w_engagement +
    w_label must sum to 1.0 for the composite to land in [0, 1].
    """
    half_life_days: float = 14.0
    reaction_weight: float = 3.0
    engagement_ceiling: float = 100.0
    label_weights: Mapping[str, float] = field(default_factory=_default_label_weights)
    label_max: float = 1.0
    w_recency: float = 0.4
    w_engagement: float = 0.4
    w_label: float = 0.2


@dataclass(frozen=True)
class ScoreBreakdown:
    """Per-issue score with every component surfaced.

    frozen=True so instances are hashable and safe to keep around.
    Reviewers should treat composite as a sort key, not as a verdict.
    """
    issue_id: str
    recency: float
    engagement: float
    label: float
    composite: float


def score_issue(issue: Issue, now: datetime, config: RankConfig) -> ScoreBreakdown:
    """Compose recency + engagement + label into a single ScoreBreakdown."""
    r = recency_score(issue, now, config.half_life_days)
    e = engagement_score(issue, config.reaction_weight, config.engagement_ceiling)
    lbl = label_score(issue, config.label_weights, config.label_max)
    composite = config.w_recency * r + config.w_engagement * e + config.w_label * lbl
    return ScoreBreakdown(
        issue_id=issue.id,
        recency=r,
        engagement=e,
        label=lbl,
        composite=composite,
    )
