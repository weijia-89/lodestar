"""CLI entry point for the moderation/PII filter.

Reads a parquet of Issue rows, scans title + body for PII patterns, and
writes the same parquet with an additional `pii_flags` list column. Does
not redact or drop rows. Reviewer decides disposition.

Usage:
    python -m voc.moderate --input X.parquet --output X-moderated.parquet
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from voc.moderate.patterns import scan_text
from voc.schema.issue import Issue


def _row_to_issue(row: dict) -> Issue:
    """Construct an Issue from a parquet row, ignoring extra columns."""
    return Issue(**{k: row[k] for k in Issue.model_fields if k in row})


def scan_issue(issue: Issue) -> list[str]:
    """Scan title + body of a single Issue. Returns deduped sorted flags."""
    flags = set(scan_text(issue.title)) | set(scan_text(issue.body))
    return sorted(flags)


def run_moderate(input: Path, output: Path) -> int:
    """Read parquet at `input`, add pii_flags column, write to `output`.

    Returns the number of rows written. Empty input writes an empty
    parquet with the pii_flags column added to the schema.
    """
    df_in = pd.read_parquet(input)
    if len(df_in) == 0:
        df_in["pii_flags"] = pd.Series(dtype="object")
        df_in.to_parquet(output, index=False)
        return 0
    flags_per_row = [
        scan_issue(_row_to_issue(row)) for row in df_in.to_dict(orient="records")
    ]
    df_out = df_in.copy()
    df_out["pii_flags"] = flags_per_row
    df_out.to_parquet(output, index=False)
    return len(df_out)


def main() -> None:
    p = argparse.ArgumentParser(prog="voc.moderate")
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    n = run_moderate(input=args.input, output=args.output)
    print(f"moderated {n} issues -> {args.output}")


if __name__ == "__main__":
    main()
