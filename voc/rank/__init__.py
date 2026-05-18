"""Candidate-ranker for the lodestar pipeline.

Takes deduplicated Issue rows and produces a top-N candidate pool with
per-component score breakdown so a human reviewer can audit and write
rationale on the top 5.

The composite score is a candidate-priority signal, NOT a severity
classification. Severity remains human judgment per the project refusal
list (see CLAUDE.md / AGENTS.md).
"""
from voc.rank.ranker import rank, top_n
from voc.rank.score import RankConfig, ScoreBreakdown

__all__ = ["RankConfig", "ScoreBreakdown", "rank", "top_n"]
