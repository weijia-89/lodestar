"""T11 Red: Dedup CLI also appends cluster_id_semantic column."""
from datetime import datetime, timezone
from pathlib import Path

import pyarrow.parquet as pq

from voc.dedup.__main__ import run_dedup
from voc.ingest.parquet_io import write_issues
from voc.schema.issue import Issue


def _i(n: int, title: str, body: str = "") -> Issue:
    return Issue(
        id=f"aider:{n}", tool="aider", repo="Aider-AI/aider", number=n,
        title=title, body=body, url=f"https://x/{n}", state="open",
        created_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
        updated_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
        closed_at=None, labels=[], author_login_sha256="a" * 64,
        comments_count=0, reactions_count=0,
    )


def test_dedup_cli_adds_both_cluster_columns(tmp_path: Path):
    src = tmp_path / "in.parquet"
    dst = tmp_path / "out.parquet"
    body_overlap = (
        "When I run aider on a large repository the agent loop "
        "hangs after the first edit and never returns control. "
        "I have to kill the process. Reproduces every time on macOS."
    )
    issues = [
        _i(1, "aider crashes on empty file", "stack trace"),
        _i(2, "crash: aider crashes on empty file", "stack trace"),  # fuzzy dup
        _i(3, "Crash on large repo", body_overlap),  # body-shared with 4
        _i(4, "Aider hangs after first edit", body_overlap + " Also on Linux."),
        _i(5, "Documentation typo", "broken link in install section"),  # singleton
    ]
    write_issues(issues, src)
    n = run_dedup(input=src, output=dst, fuzzy_threshold=85, semantic_threshold=0.5)
    assert n == 5
    table = pq.read_table(dst)
    assert "cluster_id_fuzzy" in table.column_names
    assert "cluster_id_semantic" in table.column_names
    fuzzy = table["cluster_id_fuzzy"].to_pylist()
    semantic = table["cluster_id_semantic"].to_pylist()
    # Fuzzy catches title dup
    assert fuzzy[0] == fuzzy[1]
    # Semantic catches body-shared dup
    assert semantic[2] == semantic[3]
    # Singleton stays singleton in both
    assert fuzzy.count(fuzzy[4]) == 1
    assert semantic.count(semantic[4]) == 1
