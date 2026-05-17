"""Shared fixtures for dedup tests. Single Issue factory; one place to update on schema drift."""
from datetime import datetime, timezone

import pytest

from voc.schema.issue import Issue


def _make_issue(n: int, title: str, body: str = "") -> Issue:
    return Issue(
        id=f"aider:{n}",
        tool="aider",
        repo="Aider-AI/aider",
        number=n,
        title=title,
        body=body,
        url=f"https://x/{n}",
        state="open",
        created_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
        updated_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
        closed_at=None,
        labels=[],
        author_login_sha256="a" * 64,
        comments_count=0,
        reactions_count=0,
    )


@pytest.fixture
def make_issue():
    """Factory fixture: make_issue(n, title, body='') → Issue."""
    return _make_issue
