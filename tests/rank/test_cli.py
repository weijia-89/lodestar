"""CLI smoke + parquet round-trip tests.

Task 8 of docs/superpowers/plans/2026-05-17-ranker.md. Covers falsifier
R6 (parquet round-trip preserves float64 scores).
"""
import subprocess
import sys
from datetime import timedelta

import pandas as pd

from voc.rank.__main__ import run_rank
from voc.schema.issue import Issue


def _to_parquet(issues, path):
    rows = [i.model_dump() for i in issues]
    pd.DataFrame(rows).to_parquet(path, index=False)


def test_run_rank_writes_parquet_with_score_columns(make_issue, now, tmp_path):
    src = tmp_path / "in.parquet"
    dst = tmp_path / "out.parquet"
    issues = [
        make_issue(
            1,
            labels=["bug"],
            comments_count=10,
            reactions_count=5,
            updated_at=now,
        ),
        make_issue(
            2,
            labels=[],
            comments_count=0,
            updated_at=now - timedelta(days=60),
        ),
        make_issue(3, labels=["p0"], updated_at=now - timedelta(days=2)),
    ]
    _to_parquet(issues, src)
    run_rank(input=src, output=dst, top=None, now=now)

    df = pd.read_parquet(dst)
    for col in (
        "recency_score",
        "engagement_score",
        "label_score",
        "composite_score",
        "rank",
    ):
        assert col in df.columns, f"missing column {col}"
    # rank is 1-indexed and monotone increasing in output order
    assert df["rank"].tolist() == sorted(df["rank"].tolist())
    # Highest composite should be issue 1 (fresh, labeled, engaged) or issue 3
    # (P0 label). Issue 2 (old, no engagement, no labels) should be last.
    assert df.iloc[-1]["id"] == "aider:2"


def test_run_rank_top_n_filter(make_issue, now, tmp_path):
    src = tmp_path / "in.parquet"
    dst = tmp_path / "out.parquet"
    issues = [make_issue(i, comments_count=i) for i in range(10)]
    _to_parquet(issues, src)
    run_rank(input=src, output=dst, top=3, now=now)
    df = pd.read_parquet(dst)
    assert len(df) == 3


def test_run_rank_empty_corpus_writes_empty_parquet(now, tmp_path):
    src = tmp_path / "in.parquet"
    dst = tmp_path / "out.parquet"
    pd.DataFrame(columns=list(Issue.model_fields.keys())).to_parquet(src, index=False)
    run_rank(input=src, output=dst, top=None, now=now)
    df = pd.read_parquet(dst)
    assert len(df) == 0


def test_run_rank_scores_round_trip_float64(make_issue, now, tmp_path):
    """Falsifier R6: parquet must preserve composite_score to float64 precision."""
    src = tmp_path / "in.parquet"
    dst = tmp_path / "out.parquet"
    issues = [
        make_issue(i, comments_count=i * 3, reactions_count=i, labels=["bug"])
        for i in range(5)
    ]
    _to_parquet(issues, src)
    run_rank(input=src, output=dst, top=None, now=now)
    df = pd.read_parquet(dst)
    assert df["composite_score"].dtype == "float64"
    for v in df["composite_score"]:
        assert 0.0 <= v <= 1.0


def test_run_rank_ignores_extra_columns_from_dedup_stage(make_issue, now, tmp_path):
    """When the input parquet has cluster_id columns from the dedup stage,
    the ranker must not trip on pydantic extra='forbid'.
    """
    src = tmp_path / "in.parquet"
    dst = tmp_path / "out.parquet"
    issues = [make_issue(i, comments_count=i) for i in range(3)]
    rows = [i.model_dump() for i in issues]
    df_in = pd.DataFrame(rows)
    # Simulate the dedup-stage output: extra columns we should ignore
    df_in["cluster_id_fuzzy"] = [0, 1, 2]
    df_in["cluster_id_semantic"] = [0, 1, 2]
    df_in.to_parquet(src, index=False)
    run_rank(input=src, output=dst, top=None, now=now)
    df = pd.read_parquet(dst)
    assert len(df) == 3
    assert "composite_score" in df.columns
    # Extra columns from the dedup stage flow through to the output
    assert "cluster_id_fuzzy" in df.columns


def test_run_rank_cli_invocation_via_module(make_issue, now, tmp_path):
    """End-to-end via `python -m voc.rank`."""
    src = tmp_path / "in.parquet"
    dst = tmp_path / "out.parquet"
    issues = [make_issue(i, comments_count=i * 2) for i in range(5)]
    _to_parquet(issues, src)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "voc.rank",
            "--input",
            str(src),
            "--output",
            str(dst),
            "--top",
            "3",
            "--now",
            now.isoformat(),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    df = pd.read_parquet(dst)
    assert len(df) == 3
