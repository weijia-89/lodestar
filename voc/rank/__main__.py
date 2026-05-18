"""CLI entry point for the ranker.

Reads a parquet of dedup'd Issue rows, ranks them, writes a parquet with
score columns appended. Sort order: composite_score descending, ties by
issue.id ascending.

Usage:
    python -m voc.rank --input dedup.parquet --output ranked.parquet \\
        [--top 20] [--now ISO8601]
    python -m voc.rank --input dedup.parquet --calibrate [--now ISO8601]

In rank mode, output columns added: recency_score, engagement_score,
label_score, composite_score, rank (1-indexed). Original Issue columns
preserved.

In `--calibrate` mode, reads the parquet, computes per-component score
distributions (min/max/mean/p50/p90), prints them as JSON to stdout,
and exits without writing a parquet. Useful for reviewing the score
landscape before deciding on a top-N cutoff.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from voc.rank.ranker import rank
from voc.rank.score import RankConfig, score_issue
from voc.schema.issue import Issue


def _row_to_issue(row: dict) -> Issue:
    """Construct an Issue from a parquet row, ignoring extra columns.

    We iterate Issue.model_fields rather than blindly **-splatting the
    row so a parquet with extra columns (e.g., cluster_id_fuzzy from the
    dedup stage) does not trip pydantic's extra='forbid'.
    """
    return Issue(**{k: row[k] for k in Issue.model_fields if k in row})


def calibrate(
    input: Path,
    now: datetime,
    config: RankConfig | None = None,
) -> dict:
    """Compute per-component score distribution stats for the parquet at `input`.

    Returns a dict like:

        {
            "n": 100,
            "recency":    {"min": ..., "max": ..., "mean": ..., "p50": ..., "p90": ...},
            "engagement": {...},
            "label":      {...},
            "composite":  {...},
        }

    For an empty corpus, returns {"n": 0} with no per-component blocks
    (percentiles of an empty array are undefined).
    """
    cfg = config or RankConfig()
    df_in = pd.read_parquet(input)
    if len(df_in) == 0:
        return {"n": 0}
    issues = [_row_to_issue(row) for row in df_in.to_dict(orient="records")]
    breakdowns = [score_issue(i, now, cfg) for i in issues]
    stats: dict = {"n": len(breakdowns)}
    for component in ("recency", "engagement", "label", "composite"):
        values = np.array([getattr(b, component) for b in breakdowns])
        stats[component] = {
            "min": float(values.min()),
            "max": float(values.max()),
            "mean": float(values.mean()),
            "p50": float(np.percentile(values, 50)),
            "p90": float(np.percentile(values, 90)),
        }
    return stats


def run_rank(
    input: Path,
    output: Path,
    top: int | None,
    now: datetime,
    config: RankConfig | None = None,
    calibrate: bool = False,
) -> int | dict:
    """Rank issues in `input`, write top-N (or all) to `output`. Returns row count.

    If `calibrate=True`, reads the parquet, computes per-component score
    distributions, returns them as a dict, and does NOT write any output
    parquet. The `output` argument is ignored in calibrate mode.
    """
    if calibrate:
        # The parameter shadows the module-level function name; reach for
        # it via globals() to keep the CLI flag name ergonomic.
        return globals()["calibrate"](input, now, config)
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
    p.add_argument(
        "--output",
        type=Path,
        required=False,
        help="Required unless --calibrate is set",
    )
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
    p.add_argument(
        "--calibrate",
        action="store_true",
        help="Print per-component score distribution stats; do not write output",
    )
    args = p.parse_args()
    now = datetime.fromisoformat(args.now) if args.now else datetime.now(UTC)
    if now.tzinfo is None:
        now = now.replace(tzinfo=UTC)
    if args.calibrate:
        stats = calibrate(args.input, now)
        json.dump(stats, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return
    if args.output is None:
        p.error("--output is required when --calibrate is not set")
    n = run_rank(input=args.input, output=args.output, top=args.top, now=now)
    print(f"ranked {n} issues -> {args.output}")


if __name__ == "__main__":
    main()
