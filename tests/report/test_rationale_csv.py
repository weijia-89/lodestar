"""Tests for the rationale-slot CSV emitter.

Reads a ranked parquet (output of voc.rank), writes a CSV with one row
per ranked issue plus empty columns for human-authored rationale.
"""
import csv
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from voc.rank.__main__ import run_rank
from voc.report.rationale_csv import emit_rationale_csv

RATIONALE_COLUMNS = ("rationale", "severity_assessment", "action_needed", "reviewer")

# Same gate as tests/rank/test_cli.py and tests/dedup/test_cli_smoke.py.
# Subprocess invocation crashes under mutmut's trampoline (mutmut.config is
# None in the subprocess). Skip the CLI smoke test under mutmut; the
# in-process emit_rationale_csv() tests still cover the same code path.
_UNDER_MUTMUT = Path.cwd().name == "mutants"


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


def test_emit_rationale_csv_surfaces_pii_flags_when_present(
    make_issue, now, tmp_path
):
    """pii_flags column from the moderate stage must reach the human reviewer.

    Spec source: README "Build status" + voc/moderate/__main__.py docstring.
    The moderate stage adds a pii_flags list column and never redacts or
    drops rows; the reviewer decides disposition. Therefore the rationale
    CSV emitter must surface pii_flags when the column exists in the
    ranked parquet.
    """
    src = tmp_path / "in.parquet"
    ranked = tmp_path / "ranked.parquet"
    out = tmp_path / "rationale.csv"
    _to_ranked_parquet([make_issue(1), make_issue(2)], src, ranked, now)
    # Inject a moderate-stage-shaped pii_flags column into the ranked parquet.
    df = pd.read_parquet(ranked)
    df["pii_flags"] = [["email"], []]
    df.to_parquet(ranked, index=False)
    emit_rationale_csv(input=ranked, output=out, n=2)

    with out.open() as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)
    assert "pii_flags" in header, (
        f"pii_flags missing from CSV header: {header}. "
        "voc/moderate/__main__.py promises this column reaches the reviewer."
    )
    pii_col = header.index("pii_flags")
    assert rows[0][pii_col] == "email", (
        f"row 0 pii_flags should render 'email', got {rows[0][pii_col]!r}"
    )
    assert rows[1][pii_col] == "", (
        f"row 1 pii_flags should be empty string, got {rows[1][pii_col]!r}"
    )


def test_emit_rationale_csv_with_themes_adds_column(make_issue, now, tmp_path):
    """When --themes is passed, the CSV gains a `theme_top_terms` column
    populated with pipe-joined TF-IDF top terms per cluster.

    Spec source: voc/analytics/themes.py docstring. Themes are descriptive
    of recurring vocabulary across the issue corpus; the column is
    informational for the human reviewer.
    """
    src = tmp_path / "in.parquet"
    ranked = tmp_path / "ranked.parquet"
    out = tmp_path / "rationale.csv"
    # ≥3 rows with vocabulary overlap so the clusterer produces non-empty
    # top terms; the project's TFIDF defaults need min_df=2 coverage.
    issues = [
        make_issue(1, title="crash on save", body="python crash trace when saving"),
        make_issue(2, title="crash on quit", body="python crash on quit segfault"),
        make_issue(3, title="performance slow", body="feels slow on large files"),
        make_issue(4, title="slow load time", body="application slow to start up"),
        make_issue(5, title="docs typo", body="documentation typo in readme"),
    ]
    _to_ranked_parquet(issues, src, ranked, now)
    emit_rationale_csv(input=ranked, output=out, n=5, themes=True)

    df = pd.read_csv(out)
    assert "theme_top_terms" in df.columns, (
        f"theme_top_terms missing from CSV when --themes is on. Header: {df.columns.tolist()}"
    )
    # At least one row carries non-empty terms; clusters must label some issues.
    non_empty = df["theme_top_terms"].fillna("").astype(str).str.len() > 0
    assert non_empty.any(), (
        "no row had non-empty theme_top_terms; clusterer produced no labels"
    )


def test_emit_rationale_csv_without_themes_unchanged(make_issue, now, tmp_path):
    """Without --themes, the CSV header must NOT include theme_top_terms.

    Regression gate on the additive contract: passing the flag is the only
    way the column appears. Existing pipelines and existing tests must
    continue to see the unaugmented CSV.
    """
    src = tmp_path / "in.parquet"
    ranked = tmp_path / "ranked.parquet"
    out = tmp_path / "rationale.csv"
    issues = [
        make_issue(i, title=f"issue number {i}", body=f"body text {i}")
        for i in range(5)
    ]
    _to_ranked_parquet(issues, src, ranked, now)
    emit_rationale_csv(input=ranked, output=out, n=5)  # themes defaults to False

    with out.open() as f:
        reader = csv.reader(f)
        header = next(reader)
    assert "theme_top_terms" not in header, (
        f"theme_top_terms must not appear in CSV when --themes is off. Header: {header}"
    )


@pytest.mark.skipif(_UNDER_MUTMUT, reason="subprocess + mutmut trampoline incompatible")
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
