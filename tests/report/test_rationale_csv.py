"""Tests for the rationale-slot CSV emitter.

Reads a ranked parquet (output of voc.rank), writes a CSV with one row
per ranked issue plus empty columns for human-authored rationale.
"""
import csv
import subprocess
import sys

import pandas as pd

from voc.rank.__main__ import run_rank
from voc.report.rationale_csv import emit_rationale_csv

RATIONALE_COLUMNS = ("rationale", "severity_assessment", "action_needed", "reviewer")


def _to_ranked_parquet(issues, src, dst, now):
    """Helper: write issues to src, run the ranker, return dst path."""
    rows = [i.model_dump() for i in issues]
    pd.DataFrame(rows).to_parquet(src, index=False)
    run_rank(input=src, output=dst, top=None, now=now)
    return dst


def test_emit_rationale_csv_writes_header_row(make_issue, now, tmp_path):
    """Output CSV has the expected header columns."""
    src = tmp_path / "in.parquet"
    ranked = tmp_path / "ranked.parquet"
    out = tmp_path / "rationale.csv"
    _to_ranked_parquet([make_issue(1)], src, ranked, now)
    emit_rationale_csv(input=ranked, output=out, n=5)

    with out.open() as f:
        reader = csv.reader(f)
        header = next(reader)
    expected = ("rank", "id", "url", "title", "composite_score", *RATIONALE_COLUMNS)
    for col in expected:
        assert col in header


def test_emit_rationale_csv_one_row_per_top_n(make_issue, now, tmp_path):
    """N=3 produces 3 data rows."""
    src = tmp_path / "in.parquet"
    ranked = tmp_path / "ranked.parquet"
    out = tmp_path / "rationale.csv"
    issues = [make_issue(i, comments_count=i) for i in range(10)]
    _to_ranked_parquet(issues, src, ranked, now)
    emit_rationale_csv(input=ranked, output=out, n=3)

    df = pd.read_csv(out)
    assert len(df) == 3


def test_emit_rationale_csv_caps_at_population(make_issue, now, tmp_path):
    """N larger than population caps at population size."""
    src = tmp_path / "in.parquet"
    ranked = tmp_path / "ranked.parquet"
    out = tmp_path / "rationale.csv"
    issues = [make_issue(i) for i in range(3)]
    _to_ranked_parquet(issues, src, ranked, now)
    emit_rationale_csv(input=ranked, output=out, n=100)

    df = pd.read_csv(out)
    assert len(df) == 3


def test_emit_rationale_csv_rationale_columns_are_empty(make_issue, now, tmp_path):
    """The rationale-slot columns must be empty for a human to fill in."""
    src = tmp_path / "in.parquet"
    ranked = tmp_path / "ranked.parquet"
    out = tmp_path / "rationale.csv"
    _to_ranked_parquet([make_issue(1), make_issue(2)], src, ranked, now)
    emit_rationale_csv(input=ranked, output=out, n=2)

    df = pd.read_csv(out)
    for col in RATIONALE_COLUMNS:
        assert df[col].isna().all() or (df[col] == "").all(), (
            f"{col} should be empty but had values: {df[col].tolist()}"
        )


def test_emit_rationale_csv_preserves_rank_order(make_issue, now, tmp_path):
    """CSV rows must be sorted by rank ascending (1, 2, 3, ...)."""
    src = tmp_path / "in.parquet"
    ranked = tmp_path / "ranked.parquet"
    out = tmp_path / "rationale.csv"
    issues = [make_issue(i, comments_count=i * 2) for i in range(5)]
    _to_ranked_parquet(issues, src, ranked, now)
    emit_rationale_csv(input=ranked, output=out, n=5)

    df = pd.read_csv(out)
    assert df["rank"].tolist() == [1, 2, 3, 4, 5]


def test_emit_rationale_csv_quotes_titles_with_commas(now, tmp_path, make_issue):
    """A title containing a comma must be quoted so CSV parses round-trip."""
    src = tmp_path / "in.parquet"
    ranked = tmp_path / "ranked.parquet"
    out = tmp_path / "rationale.csv"
    issues = [make_issue(1, title="bug: crash, then hang on save")]
    _to_ranked_parquet(issues, src, ranked, now)
    emit_rationale_csv(input=ranked, output=out, n=1)

    df = pd.read_csv(out)
    assert df.iloc[0]["title"] == "bug: crash, then hang on save"


def test_emit_rationale_csv_empty_input_writes_header_only(now, tmp_path):
    """Empty ranked parquet -> CSV with just a header row."""
    src = tmp_path / "in.parquet"
    out = tmp_path / "rationale.csv"
    # Construct an empty ranked-shaped parquet directly
    cols = [
        "id",
        "recency_score",
        "engagement_score",
        "label_score",
        "composite_score",
        "rank",
        "url",
        "title",
    ]
    pd.DataFrame(columns=cols).to_parquet(src, index=False)
    emit_rationale_csv(input=src, output=out, n=5)

    with out.open() as f:
        reader = csv.reader(f)
        rows = list(reader)
    assert len(rows) == 1  # header only
    for col in RATIONALE_COLUMNS:
        assert col in rows[0]


def test_emit_rationale_csv_cli_smoke(make_issue, now, tmp_path):
    """End-to-end via `python -m voc.report.rationale_csv`."""
    src = tmp_path / "in.parquet"
    ranked = tmp_path / "ranked.parquet"
    out = tmp_path / "rationale.csv"
    _to_ranked_parquet(
        [make_issue(i, comments_count=i) for i in range(5)], src, ranked, now
    )
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "voc.report.rationale_csv",
            "--input",
            str(ranked),
            "--output",
            str(out),
            "--top",
            "3",
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    df = pd.read_csv(out)
    assert len(df) == 3
