"""CLI entry point for the ranker.

Reads a parquet of dedup'd Issue rows, ranks them, writes a parquet with
score columns appended. Sort order: composite_score descending, ties by
issue.id ascending.

Usage:
    python -m voc.rank --input dedup.parquet --output ranked.parquet \\
        [--top 20] [--now ISO8601]

Output columns added: recency_score, engagement_score, label_score,
composite_score, rank (1-indexed). Original Issue columns preserved.
"""
from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from voc.rank.ranker import rank
from voc.rank.score import RankConfig
from voc.schema.issue import Issue


def _row_to_issue(row: dict) -> Issue:
    """Construct an Issue from a parquet row, ignoring extra columns.

    We iterate Issue.model_fields rather than blindly **-splatting the
    row so a parquet with extra columns (e.g., cluster_id_fuzzy from the
    dedup stage) does not trip pydantic's extra='forbid'.
    """
    return Issue(**{k: row[k] for k in Issue.model_fields if k in row})


def run_rank(
    input: Path,
    output: Path,
    top: int | None,
    now: datetime,
    config: RankConfig | None = None,
) -> int:
    """Rank issues in `input`, write top-N (or all) to `output`. Returns row count."""
    df_in = pd.read_parquet(input)
    if len(df_in) == 0:
        df_in.to_parquet(output, index=False)
        return 0
    issues = [_row_to_issue(row) for row in df_in.to_dict(orient="records")]
    breakdowns = rank(issues, now, config or RankConfig())
    if top is not None:
        breakdowns = breakdowns[:top]
    score_rows = [
        {
            "id": b.issue_id,
            "recency_score": b.recency,
            "engagement_score": b.engagement,
            "label_score": b.label,
            "composite_score": b.composite,
            "rank": idx + 1,
        }
        for idx, b in enumerate(breakdowns)
    ]
    scores_df = pd.DataFrame(score_rows)
    merged = scores_df.merge(df_in, on="id", how="left")
    merged = merged.sort_values("rank").reset_index(drop=True)
    merged.to_parquet(output, index=False)
    return len(merged)


def main() -> None:
    p = argparse.ArgumentParser(prog="voc.rank")
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument(
        "--top",
        type=int,
        default=None,
        help="Keep top N issues (default: all)",
    )
    p.add_argument(
        "--now",
        type=str,
        default=None,
        help="ISO8601 timestamp for 'now' (default: current UTC)",
    )
    args = p.parse_args()
    now = datetime.fromisoformat(args.now) if args.now else datetime.now(UTC)
    if now.tzinfo is None:
        now = now.replace(tzinfo=UTC)
    n = run_rank(input=args.input, output=args.output, top=args.top, now=now)
    print(f"ranked {n} issues -> {args.output}")


if __name__ == "__main__":
    main()
