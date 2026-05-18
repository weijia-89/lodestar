"""Rationale-slot CSV emitter for ranker output.

Reads a parquet produced by `voc.rank` (with rank, *_score, and Issue
columns) and writes a CSV with one row per top-N issue plus empty columns
for the human reviewer to fill in: rationale, severity_assessment,
action_needed, reviewer.

This closes the human-judgment loop: the ranker surfaces candidates,
the reviewer writes rationale by editing the CSV in their tool of choice.
The CSV is the artifact under review; the parquet is the data pipeline.

Severity is a column the human fills in, not one the pipeline assigns.
Per the project refusal list (AGENTS.md), the pipeline does not classify
severity.

Usage:
    python -m voc.report.rationale_csv \\
        --input ranked.parquet --output rationale.csv [--top 5]
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import pandas as pd

# The four columns the human fills in. Order matters for the CSV header;
# keeping rationale first because it carries the most weight in PQE judgment.
RATIONALE_COLUMNS = ("rationale", "severity_assessment", "action_needed", "reviewer")

# Columns we surface from the ranked parquet to give the reviewer context.
# We deliberately do NOT surface the body of the issue: long-form context
# belongs in the reviewer's browser tab, not jammed into a CSV cell.
CONTEXT_COLUMNS = (
    "rank",
    "id",
    "url",
    "title",
    "composite_score",
    "recency_score",
    "engagement_score",
    "label_score",
    "labels",
    "comments_count",
    "reactions_count",
    "state",
)


def emit_rationale_csv(input: Path, output: Path, n: int) -> int:
    """Read ranked parquet at `input`, write top-N rows to CSV at `output`.

    Returns the number of data rows written (excluding the header).
    """
    df = pd.read_parquet(input)
    if n > 0:
        df = df.head(n)
    # Filter to context columns that actually exist in the parquet.
    # If the upstream schema evolves, missing columns are skipped silently
    # rather than crashing; the human can still write rationale.
    present = [c for c in CONTEXT_COLUMNS if c in df.columns]
    with output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(list(present) + list(RATIONALE_COLUMNS))
        for _, row in df.iterrows():
            data = [_csv_cell(row[c]) for c in present]
            writer.writerow(data + [""] * len(RATIONALE_COLUMNS))
    return len(df)


def _csv_cell(value: object) -> str:
    """Render a parquet cell for CSV. Lists are joined with `|` so the CSV stays one cell."""
    if isinstance(value, list):
        return "|".join(str(x) for x in value)
    if value is None:
        return ""
    return str(value)


def main() -> None:
    p = argparse.ArgumentParser(prog="voc.report.rationale_csv")
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument(
        "--top",
        type=int,
        default=5,
        help="Top N rows to emit (default: 5)",
    )
    args = p.parse_args()
    n = emit_rationale_csv(input=args.input, output=args.output, n=args.top)
    print(f"wrote {n} rows -> {args.output}")


if __name__ == "__main__":
    main()
