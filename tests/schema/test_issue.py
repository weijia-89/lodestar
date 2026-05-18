"""T1 Red phase: Issue pydantic schema.

Tests should fail with ModuleNotFoundError until voc/schema/issue.py exists.
"""
from datetime import UTC

import pytest

from voc.schema.issue import Issue


def test_issue_requires_core_fields():
    with pytest.raises(ValueError):
        Issue(tool="aider")  # type: ignore[call-arg]  # missing required fields


def test_issue_normalizes_timestamps_to_utc():
    issue = Issue(
        id="aider:1234",
        tool="aider",
        repo="Aider-AI/aider",
        number=1234,
        title="Crash on empty file",
        body="repro: open empty file",
        url="https://github.com/Aider-AI/aider/issues/1234",
        state="open",
        created_at="2026-05-01T12:00:00-04:00",
        updated_at="2026-05-02T08:00:00Z",
        closed_at=None,
        labels=["bug"],
        author_login_sha256="anon-abc123",
        comments_count=3,
        reactions_count=5,
    )
    assert issue.created_at.tzinfo == UTC
    assert issue.updated_at.tzinfo == UTC
    assert issue.closed_at is None
    assert issue.tool == "aider"


def test_issue_rejects_unknown_tool():
    with pytest.raises(ValueError):
        Issue(
            id="x:1",
            tool="windsurf",  # type: ignore[arg-type]
            repo="x/x",
            number=1,
            title="t",
            body="",
            url="https://x",
            state="open",
            created_at="2026-05-01T00:00:00Z",
            updated_at="2026-05-01T00:00:00Z",
            closed_at=None,
            labels=[],
            author_login_sha256="a",
            comments_count=0,
            reactions_count=0,
        )
