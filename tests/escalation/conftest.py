# sdk-review F2: hook tags only; importorskip in test modules handles skip-without-deps
"""Escalation tests require optional Playwright deps; auto-mark with `escalation` for opt-in filtering."""
from pathlib import Path

import pytest

_ESCALATION_DIR = Path(__file__).resolve().parent


def pytest_collection_modifyitems(items):
    for item in items:
        if _ESCALATION_DIR in Path(item.path).parents:
            item.add_marker(pytest.mark.escalation)
