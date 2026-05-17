"""T6 Red: Idempotent ingest CLI."""
import time
from pathlib import Path
from unittest.mock import patch

from voc.ingest.__main__ import run_ingest


FAKE_BATCH = [
    {
        "number": 1,
        "title": "t",
        "body": "b",
        "html_url": "https://x/1",
        "state": "open",
        "created_at": "2026-05-01T00:00:00Z",
        "updated_at": "2026-05-02T00:00:00Z",
        "closed_at": None,
        "labels": [],
        "user": {"login": "u"},
        "comments": 0,
        "reactions": {"total_count": 0},
    }
]


class _FakeClient:
    def __init__(self, *args, **kwargs):  # absorb token=... kwarg
        pass

    def fetch_issues_since(self, repo, since):
        yield from FAKE_BATCH


def test_cli_writes_parquet_and_is_idempotent(tmp_path: Path):
    out = tmp_path / "aider.parquet"
    with patch("voc.ingest.__main__.GitHubIssuesClient", _FakeClient):
        run_ingest(tool="aider", window_days=28, output=out)
        mtime1 = out.stat().st_mtime_ns
        run_ingest(tool="aider", window_days=28, output=out)  # same window, no force
        mtime2 = out.stat().st_mtime_ns
    assert mtime1 == mtime2  # no rewrite on duplicate run within idempotency window


def test_cli_force_rewrites(tmp_path: Path):
    out = tmp_path / "aider.parquet"
    with patch("voc.ingest.__main__.GitHubIssuesClient", _FakeClient):
        run_ingest(tool="aider", window_days=28, output=out)
        mtime1 = out.stat().st_mtime_ns
        time.sleep(0.01)
        run_ingest(tool="aider", window_days=28, output=out, force=True)
        mtime2 = out.stat().st_mtime_ns
    assert mtime2 > mtime1
