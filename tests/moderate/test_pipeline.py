"""Tests for the moderation pipeline (issue-level scan + parquet output)."""
import pandas as pd

from voc.moderate.__main__ import run_moderate, scan_issue
from voc.schema.issue import Issue


def _to_parquet(issues, path):
    rows = [i.model_dump() for i in issues]
    pd.DataFrame(rows).to_parquet(path, index=False)


def test_scan_issue_returns_empty_for_clean_issue(make_issue):
    issue = make_issue(1, title="bug: crash on save", body="when I press save it crashes")
    assert scan_issue(issue) == []


def test_scan_issue_detects_pii_in_body(make_issue):
    issue = make_issue(
        1,
        title="bug",
        body="my email is alice@example.com please respond",
    )
    assert "email" in scan_issue(issue)


def test_scan_issue_detects_pii_in_title(make_issue):
    issue = make_issue(
        1,
        title="contact alice@example.com for repro",
        body="not much detail",
    )
    assert "email" in scan_issue(issue)


def test_scan_issue_unions_flags_from_title_and_body(make_issue):
    issue = make_issue(
        1,
        title="call 555-867-5309 please",
        body="my email is bob@example.com",
    )
    flags = scan_issue(issue)
    assert "phone" in flags
    assert "email" in flags


def test_run_moderate_adds_pii_flags_column(make_issue, tmp_path):
    src = tmp_path / "in.parquet"
    dst = tmp_path / "out.parquet"
    issues = [
        make_issue(1, body="contact alice@example.com"),
        make_issue(2, body="just a normal bug"),
    ]
    _to_parquet(issues, src)
    n = run_moderate(input=src, output=dst)
    assert n == 2

    df = pd.read_parquet(dst)
    assert "pii_flags" in df.columns
    by_id = {row["id"]: row for _, row in df.iterrows()}
    assert "email" in list(by_id["aider:1"]["pii_flags"])
    assert list(by_id["aider:2"]["pii_flags"]) == []


def test_run_moderate_preserves_all_original_columns(make_issue, tmp_path):
    """Adding pii_flags must not drop any existing Issue field."""
    src = tmp_path / "in.parquet"
    dst = tmp_path / "out.parquet"
    _to_parquet([make_issue(1, comments_count=7)], src)
    run_moderate(input=src, output=dst)

    df = pd.read_parquet(dst)
    for col in Issue.model_fields:
        assert col in df.columns, f"original column {col} dropped"
    assert df.iloc[0]["comments_count"] == 7


def test_run_moderate_does_not_redact_or_drop_rows(make_issue, tmp_path):
    """Moderation is flag-only. PII-containing issues stay in the output."""
    src = tmp_path / "in.parquet"
    dst = tmp_path / "out.parquet"
    pii_issue = make_issue(1, body="reach me at alice@example.com or 555-867-5309")
    _to_parquet([pii_issue], src)
    run_moderate(input=src, output=dst)

    df = pd.read_parquet(dst)
    assert len(df) == 1
    # Original body text preserved unchanged
    assert "alice@example.com" in df.iloc[0]["body"]


def test_run_moderate_empty_corpus_writes_empty_parquet(tmp_path):
    src = tmp_path / "in.parquet"
    dst = tmp_path / "out.parquet"
    pd.DataFrame(columns=list(Issue.model_fields.keys())).to_parquet(src, index=False)
    n = run_moderate(input=src, output=dst)
    assert n == 0
    df = pd.read_parquet(dst)
    assert len(df) == 0


def test_run_moderate_pii_flags_column_is_list_type(make_issue, tmp_path):
    """pii_flags must be a list (one cell, multiple flags) not a string."""
    src = tmp_path / "in.parquet"
    dst = tmp_path / "out.parquet"
    _to_parquet(
        [make_issue(1, body="alice@example.com and 555-867-5309")], src
    )
    run_moderate(input=src, output=dst)

    df = pd.read_parquet(dst)
    flags = df.iloc[0]["pii_flags"]
    # parquet may round-trip as numpy array; either is fine, but must be
    # iterable of strings, not a single concatenated string
    assert not isinstance(flags, str)
    assert "email" in list(flags)
    assert "phone" in list(flags)
