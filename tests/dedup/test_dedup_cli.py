"""T8 Red: Fuzzy dedup CLI appends cluster_id_fuzzy column."""
from datetime import datetime, timezone
from pathlib import Path

import pyarrow.parquet as pq

from voc.dedup.__main__ import run_dedup
from voc.ingest.parquet_io import write_issues
from voc.schema.issue import Issue


def _i(n: int, title: str) -> Issue:
    return Issue(
        id=f"aider:{n}", tool="aider", repo="Aider-AI/aider", number=n,
        title=title, body="", url=f"https://x/{n}", state="open",
        created_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
        updated_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
        closed_at=None, labels=[], author_login_sha256="a" * 64,
        comments_count=0, reactions_count=0,
    )


def test_dedup_cli_adds_cluster_column(tmp_path: Path):
    src = tmp_path / "in.parquet"
    dst = tmp_path / "out.parquet"
    issues = [
        _i(1, "Aider crashes on empty file"),
        _i(2, "crash: aider crashes on empty file"),  # lexical dup
        _i(3, "Memory leak in long-running sessions"),  # not a dup
    ]
    write_issues(issues, src)
    n = run_dedup(input=src, output=dst, fuzzy_threshold=85)
    assert n == 3
    table = pq.read_table(dst)
    assert "cluster_id_fuzzy" in table.column_names
    clusters = table["cluster_id_fuzzy"].to_pylist()
    assert clusters[0] == clusters[1]
    assert clusters[2] != clusters[0]
