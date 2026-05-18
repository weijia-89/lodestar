"""Shared fixtures for dedup tests. Single Issue factory; one place to update on schema drift.

mutmut+Python 3.14 compat shim: mutmut.__main__ calls `set_start_method('fork')`
at module-import time without `force=True`. When mutmut's per-mutant trampoline
re-imports mutmut.__main__ inside the test process, that fires again and crashes
because the multiprocessing context has already been set. We monkey-patch
multiprocessing.set_start_method to swallow that specific RuntimeError so the
mutation suite can run. This is harmless under normal pytest runs.
"""
import contextlib
import multiprocessing as _mp
from datetime import UTC, datetime

import pytest

_orig_set_start_method = _mp.set_start_method


def _set_start_method_silently(method, force=False):
    with contextlib.suppress(RuntimeError):
        _orig_set_start_method(method, force=force)


_mp.set_start_method = _set_start_method_silently

from voc.schema.issue import Issue  # noqa: E402


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
        created_at=datetime(2026, 5, 1, tzinfo=UTC),
        updated_at=datetime(2026, 5, 1, tzinfo=UTC),
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
