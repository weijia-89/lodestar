"""Shared fixtures for ranker tests.

Reuses the Issue factory pattern from tests/dedup/conftest.py. Single
factory function so schema drift in voc.schema.issue.Issue only touches
this one file.
"""
from datetime import UTC, datetime, timedelta

import pytest

from voc.schema.issue import Issue


def _make_issue(
    n: int,
    *,
    title: str = "issue",
    body: str = "",
    labels: list[str] | None = None,
    comments_count: int = 0,
    reactions_count: int = 0,
    updated_at: datetime | None = None,
    state: str = "open",
) -> Issue:
    if updated_at is None:
        updated_at = datetime(2026, 5, 17, tzinfo=UTC)
    return Issue(
        id=f"aider:{n}",
        tool="aider",
        repo="Aider-AI/aider",
        number=n,
        title=title,
        body=body,
        url=f"https://x/{n}",
        state=state,
        created_at=updated_at - timedelta(days=1),
        updated_at=updated_at,
        closed_at=None,
        labels=labels or [],
        author_login_sha256="a" * 64,
        comments_count=comments_count,
        reactions_count=reactions_count,
    )


@pytest.fixture
def make_issue():
    return _make_issue


@pytest.fixture
def now():
    return datetime(2026, 5, 17, tzinfo=UTC)
