"""Fixtures for report-layer tests.

Reuses the make_issue / now fixtures from tests/rank/conftest.py by
re-importing them here. Single Issue factory across the test tree.
"""
from tests.rank.conftest import make_issue, now  # noqa: F401
