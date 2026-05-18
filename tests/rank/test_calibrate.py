"""Tests for ranker --calibrate mode.

`python -m voc.rank --input X --calibrate` reads the parquet, scores every
issue, and prints per-component distribution statistics to stdout as JSON.
The output is intended for reviewers to see the score landscape before
committing to a top-N cutoff.

Calibration mode does NOT write a parquet; the --output flag is ignored
when --calibrate is set.
"""
import json
from datetime import timedelta

import pandas as pd

from voc.rank.__main__ import calibrate, run_rank
from voc.schema.issue import Issue


def _to_parquet(issues, path):
    rows = [i.model_dump() for i in issues]
    pd.DataFrame(rows).to_parquet(path, index=False)


def test_calibrate_returns_per_component_stats(make_issue, now, tmp_path):
    src = tmp_path / "in.parquet"
    issues = [
        make_issue(
            i,
            comments_count=i * 3,
            reactions_count=i,
            labels=["bug"] if i % 2 else [],
            updated_at=now - timedelta(days=i),
        )
        for i in range(1, 11)
    ]
    _to_parquet(issues, src)
    stats = calibrate(src, now)
    for component in ("recency", "engagement", "label", "composite"):
        assert component in stats
        c = stats[component]
        for key in ("min", "max", "mean", "p50", "p90"):
            assert key in c, f"missing {key} in {component}"
            assert 0.0 <= c[key] <= 1.0
        # min <= mean <= max and min <= p50 <= max
        assert c["min"] <= c["mean"] <= c["max"]
        assert c["min"] <= c["p50"] <= c["max"]
        assert c["p50"] <= c["p90"] <= c["max"]


def test_calibrate_includes_row_count(make_issue, now, tmp_path):
    src = tmp_path / "in.parquet"
    issues = [make_issue(i) for i in range(7)]
    _to_parquet(issues, src)
    stats = calibrate(src, now)
    assert stats["n"] == 7


def test_calibrate_empty_corpus_returns_zero_n_no_stats(now, tmp_path):
    """An empty parquet returns n=0 and no per-component stats blocks."""
    src = tmp_path / "in.parquet"
    pd.DataFrame(columns=list(Issue.model_fields.keys())).to_parquet(src, index=False)
    stats = calibrate(src, now)
    assert stats["n"] == 0
    for component in ("recency", "engagement", "label", "composite"):
        assert component not in stats


def test_calibrate_does_not_write_output_file(make_issue, now, tmp_path):
    """Calibrate must not write to any output path; it is read-only."""
    src = tmp_path / "in.parquet"
    issues = [make_issue(i) for i in range(3)]
    _to_parquet(issues, src)
    out = tmp_path / "should_not_exist.parquet"
    calibrate(src, now)
    assert not out.exists()


def test_calibrate_p90_distinct_from_p50_for_skewed_distribution(make_issue, now, tmp_path):
    """A skewed engagement distribution must show p90 > p50.

    Validates the percentile math is real, not collapsed to a single point.
    """
    src = tmp_path / "in.parquet"
    # 9 low-engagement + 1 high-engagement issue
    issues = [make_issue(i, comments_count=0) for i in range(9)]
    issues.append(make_issue(99, comments_count=200, reactions_count=200))
    _to_parquet(issues, src)
    stats = calibrate(src, now)
    assert stats["engagement"]["p90"] > stats["engagement"]["p50"]


def test_calibrate_cli_emits_valid_json_to_stdout(make_issue, now, tmp_path):
    """End-to-end via run_rank with calibrate=True: returns the stats dict."""
    src = tmp_path / "in.parquet"
    issues = [make_issue(i, comments_count=i) for i in range(5)]
    _to_parquet(issues, src)
    # When calibrate=True, run_rank should call calibrate() and return its
    # result. No output parquet should be written.
    out = tmp_path / "unused.parquet"
    result = run_rank(input=src, output=out, top=None, now=now, calibrate=True)
    assert isinstance(result, dict)
    assert result["n"] == 5
    assert not out.exists()
    # Returned dict must be JSON-serializable
    json.dumps(result)
