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
    "pii_flags",
    "theme_top_terms",
    "comments_count",
    "reactions_count",
    "state",
)

# Below this row count we skip clustering and emit empty theme cells.
# TF-IDF + KMeans on <3 documents produces degenerate output even when
# the vectorizer doesn't outright error.
_THEMES_MIN_ROWS = 3


def emit_rationale_csv(
    input: Path,
    output: Path,
    n: int,
    *,
    themes: bool = False,
) -> int:
    """Read ranked parquet at `input`, write top-N rows to CSV at `output`.

    When `themes=True`, augment the output with a `theme_top_terms` column
    derived from TF-IDF + MiniBatchKMeans clustering over the top-N
    rows. When fewer than 3 rows are present, the column is emitted with
    empty cells; clustering on so few docs is not informative.

    Returns the number of data rows written (excluding the header).
    """
    df = pd.read_parquet(input)
    if n > 0:
        df = df.head(n)

    if themes:
        df = _attach_theme_top_terms(df)

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


def _attach_theme_top_terms(df: pd.DataFrame) -> pd.DataFrame:
    """Add a `theme_top_terms` column to `df` via TF-IDF clustering.

    When `df` has fewer than `_THEMES_MIN_ROWS` rows, the column is added
    with empty strings; clustering on so few rows is not informative.
    The function never mutates `df` in place; it returns a new frame.
    """
    if len(df) < _THEMES_MIN_ROWS or "id" not in df.columns:
        return df.assign(theme_top_terms=[""] * len(df))

    # Build the (id, title, body) frame the clusterer expects. The body
    # column is optional in the upstream parquet (ingest may emit empty
    # bodies); fall back to "" when missing.
    body_col: pd.Series
    if "body" in df.columns:
        body_col = df["body"].fillna("").astype(str)
    else:
        body_col = pd.Series([""] * len(df), index=df.index, dtype="string")
    theme_df = pd.DataFrame(
        {
            "id": df["id"].astype(str).reset_index(drop=True),
            "title": df["title"].fillna("").astype(str).reset_index(drop=True),
            "body": body_col.reset_index(drop=True),
        }
    )

    # Local import keeps the analytics dependency out of the hot path
    # for callers that never pass --themes.
    from voc.analytics.themes import cluster_themes

    clusters = cluster_themes(theme_df)
    terms_by_id: dict[str, str] = {}
    for theme in clusters.values():
        joined = "|".join(theme.top_terms)
        for issue_id in theme.issue_ids:
            terms_by_id[issue_id] = joined
    theme_terms = [terms_by_id.get(str(iid), "") for iid in df["id"]]
    return df.assign(theme_top_terms=theme_terms)


def _csv_cell(value: object) -> str:
    """Render a parquet cell for CSV. Lists/arrays are joined with `|` so the CSV stays one cell."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (list, tuple)):
        return "|".join(str(x) for x in value)
    # pyarrow round-trips list columns as numpy.ndarray rather than list.
    # Without this branch, labels and pii_flags render as repr strings.
    if hasattr(value, "__iter__") and hasattr(value, "tolist"):
        return "|".join(str(x) for x in value)
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
    p.add_argument(
        "--themes",
        action="store_true",
        help=(
            "Augment the CSV with a `theme_top_terms` column derived from "
            "TF-IDF + MiniBatchKMeans clustering. Descriptive only."
        ),
    )
    args = p.parse_args()
    n = emit_rationale_csv(
        input=args.input,
        output=args.output,
        n=args.top,
        themes=args.themes,
    )
    print(f"wrote {n} rows -> {args.output}")


if __name__ == "__main__":
    main()
