"""T5 Red: Parquet round-trip for Issue model (closes A8)."""
from datetime import UTC, datetime
from pathlib import Path

from voc.ingest.parquet_io import read_issues, write_issues
from voc.schema.issue import Issue


def _make_issue(n: int) -> Issue:
    return Issue(
        id=f"aider:{n}",
        tool="aider",
        repo="Aider-AI/aider",
        number=n,
        title=f"t{n}",
        body=f"b{n}",
        url=f"https://x/{n}",
        state="open",
        created_at=datetime(2026, 5, 1, tzinfo=UTC),
        updated_at=datetime(2026, 5, 2, tzinfo=UTC),
        closed_at=None,
        labels=["bug", "ux"] if n % 2 else [],
        author_login_sha256="a" * 64,
        comments_count=n,
        reactions_count=n * 2,
    )


def test_parquet_round_trip_preserves_all_fields(tmp_path: Path):
    originals = [_make_issue(i) for i in range(50)]
    path = tmp_path / "out.parquet"
    write_issues(originals, path)
    loaded = list(read_issues(path))
    assert len(loaded) == 50
    for a, b in zip(originals, loaded, strict=True):
        assert a == b  # pydantic frozen __eq__


def test_parquet_round_trip_preserves_empty_corpus(tmp_path: Path):
    path = tmp_path / "empty.parquet"
    write_issues([], path)
    loaded = list(read_issues(path))
    assert loaded == []
